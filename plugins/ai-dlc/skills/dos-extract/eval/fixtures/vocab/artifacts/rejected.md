# Spec — settlement rework

Each Txn inside a SettlementBatch must balance before the batch closes. The Txn list is
frozen once the Window closes; a Posting outside the Window is queued for the next batch.
