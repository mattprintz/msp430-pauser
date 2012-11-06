#include "msp430.h"
#include "stdbool.h"

#include "stdlib.h"

#define TXD BIT1							// TXD on P1.1
#define RXD BIT2							// RXD on P1.2

#define BTN BIT3

#define Bitime 104							// 9600 Baud
#define Bitime_5 52							// Half bit

#define STATE_WAITING	0x00
#define STATE_SYNCING	0x01
#define STATE_RUNNING	0x02

#define REG_CODE		"5617"

unsigned char code[] = "5617";

unsigned int TXByte;
unsigned char BitCnt;
unsigned int RXByte;

unsigned int state = STATE_WAITING;

bool isReceiving; // Status for when the device is receiving
bool hasReceived; // Lets the program know when a byte is received
bool hasClick;

bool ADCDone; // ADC Done flag
unsigned int ADCValue; // Measured ADC Value

// Function Definitions
void Transmit(void);
void Receive(void);

void Register(void);

void Click(void);

void main(void) {
	
	WDTCTL = WDTPW + WDTHOLD; // Stop WDT
	
	BCSCTL1 = CALBC1_1MHZ; // Set range
	DCOCTL = CALDCO_1MHZ; // SMCLK = DCO = 1MHz
	
	P1SEL |= TXD; // Connected TXD to timer
	P1DIR |= TXD;
	
	P1IES |= RXD; // RXD Hi/lo edge interrupt
	P1IFG &= ~RXD; // Clear RXD (flag) before enabling interrupt
	P1IE |= RXD; // Enable RXD interrupt
	
	P1DIR |= BIT0;
	P1OUT &= ~BIT0; // Turn off LED at P1.0
	
	P1DIR &= ~BTN;
	P1IES |= BTN;
	P1IFG &= ~BTN;
	P1IE |= BTN;
	
	isReceiving = false; // Set initial values
	hasReceived = false;
	hasClick = false;
	
	__bis_SR_register(GIE); // interrupts enabled
	while(1) {
		if (hasReceived) { // If the device has recieved a value
			Receive();
		}
		if(hasClick) {
			Click();
		}
	}
}


void Transmit() {
   while(isReceiving); // Wait for RX completion

   TXByte |= 0x100; // Add stop bit to TXByte (which is logical 1)
   TXByte = TXByte << 1; // Add start bit (which is logical 0)
   BitCnt = 0xA; // Load Bit counter, 8 bits + ST/SP
  
   CCTL0 = OUT; // TXD Idle as Mark
   TACTL = TASSEL_2 + MC_2; // SMCLK, continuous mode
   CCR0 = TAR; // Initialize compare register
   CCR0 += Bitime; // Set time till first bit
   CCTL0 = CCIS0 + OUTMOD0 + CCIE; // Set signal, intial value, enable interrupts
   while ( CCTL0 & CCIE ); // Wait for previous TX completion
	
}

void Receive() {
	hasReceived = false; // Clear the flag
	
	if(state == STATE_WAITING && RXByte == 0x21) {
		TXByte = 0x23;
		Transmit();
		state = STATE_SYNCING;
	}
	else if(state == STATE_SYNCING && RXByte == 0x23) {
		Register();
		state = STATE_RUNNING;
	}
	else if(state == STATE_RUNNING && RXByte != 0x5A) {
		TXByte = 0x2B;
		Transmit();
	}
	else if (state == STATE_RUNNING && RXByte == 0x5A) {
		state = STATE_WAITING;
		P1OUT &= ~BIT0;
	}
}

void Register() {
		
	int i;
	for(i = 0; i < sizeof(code); i++) {
		TXByte = code[i];
		Transmit();
	}
	
}


void Click() {
	hasClick = false;
	
	TXByte = 0x56;
	Transmit();
	
}

/**
* ADC interrupt routine. Pulls CPU out of sleep mode for the main loop.
**/
#pragma vector=ADC10_VECTOR
__interrupt void ADC10_ISR (void) {
	ADCValue = ADC10MEM; // Saves measured value.
	ADCDone = true; // Sets flag for main loop.
   __bic_SR_register_on_exit(CPUOFF); // Enable CPU so the main while loop continues
}

/**
* Starts the receive timer, and disables any current transmission.
**/
#pragma vector=PORT1_VECTOR
__interrupt void Port_1(void) {
	
	if((RXD & P1IFG) == RXD) {
		isReceiving = true;
		
		P1IE &= ~RXD; // Disable RXD interrupt
		P1IFG &= ~RXD; // Clear RXD IFG (interrupt flag)
	
		TACTL = TASSEL_2 + MC_2; // SMCLK, continuous mode
		CCR0 = TAR; // Initialize compare register
		CCR0 += Bitime_5; // Set time till first bit
		CCTL0 = OUTMOD1 + CCIE; // Disable TX and enable interrupts
		
		RXByte = 0; // Initialize RXByte
		BitCnt = 0x9; // Load Bit counter, 8 bits + ST
	} 
	else if((BTN & P1IFG) == BTN) {
				
		P1IFG &= ~BTN; // Clear BTN IFG (interrupt flag)
		P1IES ^= BTN; //
		
		if(state == STATE_RUNNING) { 
			hasClick = true;
		}
		
	}
	
}

/**
* Timer interrupt routine. This handles transmiting and receiving bytes.
**/
#pragma vector=TIMERA0_VECTOR
__interrupt void Timer_A (void) {
	if(!isReceiving) {
		CCR0 += Bitime; // Add Offset to CCR0
		if ( BitCnt == 0) { // If all bits TXed
			TACTL = TASSEL_2; // SMCLK, timer off (for power consumption)
			CCTL0 &= ~ CCIE ; // Disable interrupt
		}
		else {
			CCTL0 |= OUTMOD2; // Set TX bit to 0
			if (TXByte & 0x01)
				CCTL0 &= ~ OUTMOD2; // If it should be 1, set it to 1
			TXByte = TXByte >> 1;
			BitCnt --;
		}
	}
	else {
		CCR0 += Bitime; // Add Offset to CCR0
		if ( BitCnt == 0) {
			TACTL = TASSEL_2; // SMCLK, timer off (for power consumption)
			CCTL0 &= ~ CCIE ; // Disable interrupt
			
			isReceiving = false;
			
			P1IFG &= ~RXD; // clear RXD IFG (interrupt flag)
			P1IE |= RXD; // enabled RXD interrupt

			if ( (RXByte & 0x201) == 0x200) { // Validate the start and stop bits are correct
				RXByte = RXByte >> 1; // Remove start bit
				RXByte &= 0xFF; // Remove stop bit
				hasReceived = true;
			}
   			__bic_SR_register_on_exit(CPUOFF); // Enable CPU so the main while loop continues
		}
		else {
			if ( (P1IN & RXD) == RXD) // If bit is set?
				RXByte |= 0x400; // Set the value in the RXByte
			RXByte = RXByte >> 1; // Shift the bits down
			BitCnt --;
		}
	}
}

