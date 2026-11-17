# model-b：生成者 B 的说明（Quint quint-modeling Step 7 handoff）

## What it covers

- 同一份合同下的另一种建模：没有单独的 read 步骤，提交即判定；售罄后允许同一用户再次提交。
- 合同性质在 STOCK=1、两个用户的范围内检查。

## What it does NOT cover

- 页面展示的剩余数量（read）没有建模，因此“读到旧值后提交”的交错不在这个模型里。
- 支付、退款、超时释放、崩溃恢复、多场次、补货。

## When to update

- 如果确认不允许售罄后重试（见 model-divergence 的裁决），删除重试动作再比较。
