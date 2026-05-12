       IDENTIFICATION DIVISION.
       PROGRAM-ID. CUSTBILL.
       AUTHOR. MANOHARAN MUDALIAR.
       DATE-WRITTEN. 2024-01-15.
      *----------------------------------------------------------------*
      * PROGRAM: CUSTBILL                                              *
      * PURPOSE: CUSTOMER BILLING CALCULATION                         *
      *          READS CUSTOMER FILE, CALCULATES BILL AMOUNTS,        *
      *          APPLIES DISCOUNTS AND WRITES OUTPUT TO BILLING FILE  *
      *----------------------------------------------------------------*

       ENVIRONMENT DIVISION.
       INPUT-OUTPUT SECTION.
       FILE-CONTROL.
           SELECT CUSTOMER-FILE
               ASSIGN TO 'CUSTMAST'
               ORGANIZATION IS SEQUENTIAL.
           SELECT BILLING-FILE
               ASSIGN TO 'BILLOUT'
               ORGANIZATION IS SEQUENTIAL.
           SELECT ERROR-FILE
               ASSIGN TO 'ERROUT'
               ORGANIZATION IS SEQUENTIAL.

       DATA DIVISION.
       FILE SECTION.
       FD  CUSTOMER-FILE.
       01  CUSTOMER-RECORD.
           05  CUST-ID             PIC X(10).
           05  CUST-NAME           PIC X(30).
           05  CUST-TYPE           PIC X(02).
               88  CUST-RESIDENTIAL    VALUE 'RE'.
               88  CUST-COMMERCIAL     VALUE 'CO'.
               88  CUST-INDUSTRIAL     VALUE 'IN'.
           05  CUST-USAGE          PIC 9(07)V99.
           05  CUST-PREV-BALANCE   PIC S9(09)V99.
           05  CUST-STATUS         PIC X(01).
               88  CUST-ACTIVE         VALUE 'A'.
               88  CUST-INACTIVE       VALUE 'I'.
               88  CUST-SUSPENDED      VALUE 'S'.

       FD  BILLING-FILE.
       01  BILLING-RECORD.
           05  BILL-CUST-ID        PIC X(10).
           05  BILL-CUST-NAME      PIC X(30).
           05  BILL-USAGE          PIC 9(07)V99.
           05  BILL-BASE-AMOUNT    PIC S9(09)V99.
           05  BILL-DISCOUNT       PIC S9(07)V99.
           05  BILL-TAX            PIC S9(07)V99.
           05  BILL-TOTAL          PIC S9(09)V99.
           05  BILL-STATUS         PIC X(10).

       FD  ERROR-FILE.
       01  ERROR-RECORD            PIC X(80).

       WORKING-STORAGE SECTION.
       01  WS-FLAGS.
           05  WS-EOF              PIC X(01) VALUE 'N'.
               88  END-OF-FILE         VALUE 'Y'.
           05  WS-ERROR-FLAG       PIC X(01) VALUE 'N'.

       01  WS-COUNTERS.
           05  WS-RECORDS-READ     PIC 9(07) VALUE ZERO.
           05  WS-RECORDS-WRITTEN  PIC 9(07) VALUE ZERO.
           05  WS-RECORDS-SKIPPED  PIC 9(07) VALUE ZERO.
           05  WS-ERROR-COUNT      PIC 9(05) VALUE ZERO.

       01  WS-RATES.
           05  WS-RESIDENTIAL-RATE PIC 9(03)V999 VALUE 0.125.
           05  WS-COMMERCIAL-RATE  PIC 9(03)V999 VALUE 0.175.
           05  WS-INDUSTRIAL-RATE  PIC 9(03)V999 VALUE 0.145.
           05  WS-TAX-RATE         PIC 9(03)V999 VALUE 0.085.

       01  WS-DISCOUNT-THRESHOLDS.
           05  WS-HIGH-USAGE       PIC 9(07)   VALUE 5000000.
           05  WS-MED-USAGE        PIC 9(07)   VALUE 1000000.
           05  WS-HIGH-DISC-RATE   PIC 9(03)V99 VALUE 0.10.
           05  WS-MED-DISC-RATE    PIC 9(03)V99 VALUE 0.05.

       01  WS-CALC-FIELDS.
           05  WS-BASE-AMOUNT      PIC S9(09)V99 VALUE ZERO.
           05  WS-DISCOUNT-AMT     PIC S9(07)V99 VALUE ZERO.
           05  WS-TAX-AMT          PIC S9(07)V99 VALUE ZERO.
           05  WS-TOTAL-AMT        PIC S9(09)V99 VALUE ZERO.
           05  WS-RATE-USED        PIC 9(03)V999 VALUE ZERO.
           05  WS-DISC-RATE-USED   PIC 9(03)V99  VALUE ZERO.

       01  WS-ERROR-MSG            PIC X(80).
       01  WS-CURRENT-DATE.
           05  WS-YEAR             PIC 9(04).
           05  WS-MONTH            PIC 9(02).
           05  WS-DAY              PIC 9(02).

       PROCEDURE DIVISION.
       0000-MAIN.
           PERFORM 1000-INITIALIZE
           PERFORM 2000-PROCESS UNTIL END-OF-FILE
           PERFORM 3000-FINALIZE
           STOP RUN.

       1000-INITIALIZE.
           OPEN INPUT  CUSTOMER-FILE
           OPEN OUTPUT BILLING-FILE
           OPEN OUTPUT ERROR-FILE
           MOVE FUNCTION CURRENT-DATE(1:8) TO WS-CURRENT-DATE
           PERFORM 1100-READ-CUSTOMER.

       1100-READ-CUSTOMER.
           READ CUSTOMER-FILE
               AT END MOVE 'Y' TO WS-EOF
           END-READ.

       2000-PROCESS.
           ADD 1 TO WS-RECORDS-READ
           PERFORM 2100-VALIDATE-RECORD
           IF WS-ERROR-FLAG = 'N'
               PERFORM 2200-CALCULATE-BILL
               PERFORM 2300-WRITE-BILLING
           END-IF
           PERFORM 1100-READ-CUSTOMER.

       2100-VALIDATE-RECORD.
           MOVE 'N' TO WS-ERROR-FLAG
           IF NOT CUST-ACTIVE
               MOVE 'Y' TO WS-ERROR-FLAG
               STRING 'SKIPPED: CUST-ID=' CUST-ID
                      ' STATUS=' CUST-STATUS
                      DELIMITED SIZE INTO WS-ERROR-MSG
               WRITE ERROR-RECORD FROM WS-ERROR-MSG
               ADD 1 TO WS-RECORDS-SKIPPED
           END-IF
           IF CUST-USAGE = ZERO AND WS-ERROR-FLAG = 'N'
               MOVE 'Y' TO WS-ERROR-FLAG
               STRING 'ZERO USAGE: CUST-ID=' CUST-ID
                      DELIMITED SIZE INTO WS-ERROR-MSG
               WRITE ERROR-RECORD FROM WS-ERROR-MSG
               ADD 1 TO WS-ERROR-COUNT
           END-IF.

       2200-CALCULATE-BILL.
           EVALUATE TRUE
               WHEN CUST-RESIDENTIAL
                   MOVE WS-RESIDENTIAL-RATE TO WS-RATE-USED
               WHEN CUST-COMMERCIAL
                   MOVE WS-COMMERCIAL-RATE  TO WS-RATE-USED
               WHEN CUST-INDUSTRIAL
                   MOVE WS-INDUSTRIAL-RATE  TO WS-RATE-USED
               WHEN OTHER
                   MOVE WS-COMMERCIAL-RATE  TO WS-RATE-USED
           END-EVALUATE

           COMPUTE WS-BASE-AMOUNT =
               CUST-USAGE * WS-RATE-USED

           EVALUATE TRUE
               WHEN CUST-USAGE > WS-HIGH-USAGE
                   MOVE WS-HIGH-DISC-RATE TO WS-DISC-RATE-USED
               WHEN CUST-USAGE > WS-MED-USAGE
                   MOVE WS-MED-DISC-RATE  TO WS-DISC-RATE-USED
               WHEN OTHER
                   MOVE ZERO TO WS-DISC-RATE-USED
           END-EVALUATE

           COMPUTE WS-DISCOUNT-AMT =
               WS-BASE-AMOUNT * WS-DISC-RATE-USED

           COMPUTE WS-TAX-AMT =
               (WS-BASE-AMOUNT - WS-DISCOUNT-AMT) * WS-TAX-RATE

           COMPUTE WS-TOTAL-AMT =
               WS-BASE-AMOUNT - WS-DISCOUNT-AMT + WS-TAX-AMT
               + CUST-PREV-BALANCE.

       2300-WRITE-BILLING.
           MOVE CUST-ID          TO BILL-CUST-ID
           MOVE CUST-NAME        TO BILL-CUST-NAME
           MOVE CUST-USAGE       TO BILL-USAGE
           MOVE WS-BASE-AMOUNT   TO BILL-BASE-AMOUNT
           MOVE WS-DISCOUNT-AMT  TO BILL-DISCOUNT
           MOVE WS-TAX-AMT       TO BILL-TAX
           MOVE WS-TOTAL-AMT     TO BILL-TOTAL
           MOVE 'PROCESSED'      TO BILL-STATUS
           WRITE BILLING-RECORD
           ADD 1 TO WS-RECORDS-WRITTEN.

       3000-FINALIZE.
           DISPLAY 'CUSTBILL EXECUTION SUMMARY'
           DISPLAY '=========================='
           DISPLAY 'RECORDS READ    : ' WS-RECORDS-READ
           DISPLAY 'RECORDS WRITTEN : ' WS-RECORDS-WRITTEN
           DISPLAY 'RECORDS SKIPPED : ' WS-RECORDS-SKIPPED
           DISPLAY 'ERROR COUNT     : ' WS-ERROR-COUNT
           CLOSE CUSTOMER-FILE
           CLOSE BILLING-FILE
           CLOSE ERROR-FILE.
