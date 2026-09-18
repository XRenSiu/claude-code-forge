# Spec — ledger rework

Each BankingTransaction inside a SettlementBatch must balance before it closes. Every
Posting outside the ClearingWindow is queued for the next run; the Account keeps its RateWindow.
