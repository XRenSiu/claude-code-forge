# 实现备注

入口在 `LedgerPoster.post()`，配置读 config/settlement_window.yaml，
脚本是 tools/replay_batch.py。文档见 https://example.com/InternalWiki/PostingRules。

```python
class LedgerRepository:
    def find_by_account(self, account_id): ...
    settlement_window = 15
```

~~~
UnfencedButTilded = "AlsoNotProse"
~~~

每笔 BankingTransaction 走 R001。
