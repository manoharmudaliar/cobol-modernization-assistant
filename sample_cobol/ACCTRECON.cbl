       IDENTIFICATION DIVISION.
       PROGRAM-ID. ACCTRECON.
       AUTHOR. MANOHARAN MUDALIAR.
      *----------------------------------------------------------------*
      * PROGRAM: ACCTRECON                                             *
      * PURPOSE: ACCOUNT RECONCILIATION BETWEEN TWO DATA SOURCES      *
      *          COMPARES MAINFRAME BALANCES VS EXTERNAL SYSTEM        *
      *          FLAGS OUT-OF-BALANCE RECORDS FOR REVIEW              *
      *----------------------------------------------------------------*

       ENVIRONMENT DIVISION.
       INPUT-OUTPUT SECTION.
       FILE-CONTROL.
           SELECT MAINFRAME-FILE
               ASSIGN TO 'MFBALANCE'
               ORGANIZATION IS SEQUENTIAL.
           SELECT EXTERNAL-FILE
               ASSIGN TO 'EXTBALANCE'
               ORGANIZATION IS SEQUENTIAL.
           SELECT RECON-OUT-FILE
               ASSIGN TO 'RECONOUT'
               ORGANIZATION IS SEQUENTIAL.

       DATA DIVISION.
       FILE SECTION.
       FD  MAINFRAME-FILE.
       01  MF-RECORD.
           05  MF-ACCOUNT-ID       PIC X(12).
           05  MF-ACCOUNT-NAME     PIC X(25).
           05  MF-BALANCE          PIC S9(11)V99.
           05  MF-LAST-UPDATE      PIC X(08).
           05  MF-CURRENCY         PIC X(03).

       FD  EXTERNAL-FILE.
       01  EXT-RECORD.
           05  EXT-ACCOUNT-ID      PIC X(12).
           05  EXT-BALANCE         PIC S9(11)V99.
           05  EXT-LAST-UPDATE     PIC X(08).

       FD  RECON-OUT-FILE.
       01  RECON-RECORD.
           05  RC-ACCOUNT-ID       PIC X(12).
           05  RC-ACCOUNT-NAME     PIC X(25).
           05  RC-MF-BALANCE       PIC S9(11)V99.
           05  RC-EXT-BALANCE      PIC S9(11)V99.
           05  RC-DIFFERENCE       PIC S9(11)V99.
           05  RC-STATUS           PIC X(15).

       WORKING-STORAGE SECTION.
       01  WS-FLAGS.
           05  WS-MF-EOF           PIC X VALUE 'N'.
           05  WS-EXT-EOF          PIC X VALUE 'N'.

       01  WS-COUNTERS.
           05  WS-MATCHED          PIC 9(07) VALUE ZERO.
           05  WS-OUT-OF-BALANCE   PIC 9(07) VALUE ZERO.
           05  WS-MF-ONLY          PIC 9(07) VALUE ZERO.
           05  WS-EXT-ONLY         PIC 9(07) VALUE ZERO.

       01  WS-TOLERANCE            PIC 9(05)V99 VALUE 0.01.
       01  WS-DIFFERENCE           PIC S9(11)V99 VALUE ZERO.
       01  WS-ABS-DIFF             PIC 9(11)V99  VALUE ZERO.

       PROCEDURE DIVISION.
       0000-MAIN.
           PERFORM 1000-INITIALIZE
           PERFORM 2000-RECONCILE
               UNTIL WS-MF-EOF = 'Y' AND WS-EXT-EOF = 'Y'
           PERFORM 3000-FINALIZE
           STOP RUN.

       1000-INITIALIZE.
           OPEN INPUT  MAINFRAME-FILE
           OPEN INPUT  EXTERNAL-FILE
           OPEN OUTPUT RECON-OUT-FILE
           PERFORM 1100-READ-MAINFRAME
           PERFORM 1200-READ-EXTERNAL.

       1100-READ-MAINFRAME.
           READ MAINFRAME-FILE
               AT END MOVE 'Y' TO WS-MF-EOF
           END-READ.

       1200-READ-EXTERNAL.
           READ EXTERNAL-FILE
               AT END MOVE 'Y' TO WS-EXT-EOF
           END-READ.

       2000-RECONCILE.
           EVALUATE TRUE
               WHEN WS-MF-EOF = 'Y' AND WS-EXT-EOF = 'N'
                   PERFORM 2400-EXT-ONLY
               WHEN WS-MF-EOF = 'N' AND WS-EXT-EOF = 'Y'
                   PERFORM 2300-MF-ONLY
               WHEN MF-ACCOUNT-ID = EXT-ACCOUNT-ID
                   PERFORM 2100-COMPARE-BALANCES
               WHEN MF-ACCOUNT-ID < EXT-ACCOUNT-ID
                   PERFORM 2300-MF-ONLY
               WHEN MF-ACCOUNT-ID > EXT-ACCOUNT-ID
                   PERFORM 2400-EXT-ONLY
           END-EVALUATE.

       2100-COMPARE-BALANCES.
           COMPUTE WS-DIFFERENCE = MF-BALANCE - EXT-BALANCE
           COMPUTE WS-ABS-DIFF   = FUNCTION ABS(WS-DIFFERENCE)
           MOVE MF-ACCOUNT-ID    TO RC-ACCOUNT-ID
           MOVE MF-ACCOUNT-NAME  TO RC-ACCOUNT-NAME
           MOVE MF-BALANCE       TO RC-MF-BALANCE
           MOVE EXT-BALANCE      TO RC-EXT-BALANCE
           MOVE WS-DIFFERENCE    TO RC-DIFFERENCE
           IF WS-ABS-DIFF <= WS-TOLERANCE
               MOVE 'MATCHED'    TO RC-STATUS
               ADD 1 TO WS-MATCHED
           ELSE
               MOVE 'OUT-OF-BALANCE' TO RC-STATUS
               ADD 1 TO WS-OUT-OF-BALANCE
           END-IF
           WRITE RECON-RECORD
           PERFORM 1100-READ-MAINFRAME
           PERFORM 1200-READ-EXTERNAL.

       2300-MF-ONLY.
           MOVE MF-ACCOUNT-ID    TO RC-ACCOUNT-ID
           MOVE MF-ACCOUNT-NAME  TO RC-ACCOUNT-NAME
           MOVE MF-BALANCE       TO RC-MF-BALANCE
           MOVE ZERO             TO RC-EXT-BALANCE
           MOVE MF-BALANCE       TO RC-DIFFERENCE
           MOVE 'MF-ONLY'        TO RC-STATUS
           ADD 1 TO WS-MF-ONLY
           WRITE RECON-RECORD
           PERFORM 1100-READ-MAINFRAME.

       2400-EXT-ONLY.
           MOVE EXT-ACCOUNT-ID   TO RC-ACCOUNT-ID
           MOVE SPACES           TO RC-ACCOUNT-NAME
           MOVE ZERO             TO RC-MF-BALANCE
           MOVE EXT-BALANCE      TO RC-EXT-BALANCE
           MOVE EXT-BALANCE      TO RC-DIFFERENCE
           MOVE 'EXT-ONLY'       TO RC-STATUS
           ADD 1 TO WS-EXT-ONLY
           WRITE RECON-RECORD
           PERFORM 1200-READ-EXTERNAL.

       3000-FINALIZE.
           DISPLAY 'RECONCILIATION SUMMARY'
           DISPLAY 'MATCHED       : ' WS-MATCHED
           DISPLAY 'OUT-OF-BALANCE: ' WS-OUT-OF-BALANCE
           DISPLAY 'MF-ONLY       : ' WS-MF-ONLY
           DISPLAY 'EXT-ONLY      : ' WS-EXT-ONLY
           CLOSE MAINFRAME-FILE
           CLOSE EXTERNAL-FILE
           CLOSE RECON-OUT-FILE.
