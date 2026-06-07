# 实验状态说明

本文档用于说明 `GREdit / GenRecEdit` 这条实验线在 **2026 年 6 月 7 日** 的实际推进状态。它的目标不是包装结果，而是把“目前已经做到了什么、还没有做到什么”写清楚，方便公开阅读和后续迭代。

## 当前阶段

目前项目已经从“代码整理完成”推进到“编辑产物已经生成，并拿到了第一版可比较指标”的阶段。

已经确认完成的部分包括：

- 基础推荐模型 checkpoint 已就位：
  - `data/ckpt/TIGER_Cell_Phones_and_Accessories/genrec_default_ori.pth`
- 编辑请求文件已存在：
  - `data/Edit/Cell_Phones_and_Accessories/edit_requests_smoke10.json`
  - `data/Edit/Cell_Phones_and_Accessories/edit_requests_cold_test_augmented_10.json`
- 已生成的编辑结果：
  - `results/Cell_Phones_and_Accessories/deltaW_edit_requests_smoke10_1000_5.pt`
  - `results/Cell_Phones_and_Accessories/deltaW_edit_requests_micro10_1000_5.pt`

这意味着项目已经不再只是“脚本能启动”，而是已经完成了至少两组真实的模型编辑求解。

## 第一版可比较结果

为了先验证链路是否闭环，我在同一类别、同一基础 checkpoint、同一 `test` 切分下，做了一版最小可比较评估。为了避免评估阶段显存溢出，这一版使用了较保守的评估配置：

- `eval_batch_size = 16`
- `num_beams = 10`
- `topk = [10]`
- `eval_split = test`

对应结果如下：

| 设置 | iid_ratio@10 | ndcg@10 |
| --- | ---: | ---: |
| baseline | 0.6306354999542236 | 0.0022662023548036814 |
| `micro10 deltaW` | 0.6302555561065674 | 0.002245022216811776 |

从这组结果看，`micro10` 这次编辑后的数值**略低于** baseline。

如果你想直接看结构化结果表，可以参考 [experiment_results_20260607.md](./experiment_results_20260607.md)。
如果你想看通过服务器同步脚本实时刷新的版本，可以看 [experiment_results_latest.md](./experiment_results_latest.md)。

## 目前能说什么，不能说什么

基于现有证据，可以合理表达的结论是：

- 项目已经具备了从基础模型、编辑请求、模型编辑到推荐评估的闭环能力；
- 第一版 `micro10` 编辑实验已经能产出真实可比指标；
- 当前这组首轮结果没有显示出对 baseline 的提升。

基于现有证据，**不能**直接表达的结论是：

- 不能说该方法已经优于论文方法；
- 不能说编辑一定会带来推荐质量提升；
- 不能把 `micro10` 的这组结果外推成正式结论。

## 为什么还不能下最终结论

当前仍有三个限制：

1. 现有结果首先是“链路验证”和“首轮趋势观察”，还不是正式大规模实验。
2. 目前公开记录里最完整的可比结果来自 `micro10`，而不是更接近正式设定的 `cold_test_augmented_10`。
3. 即便后续指标变好，也仍然需要和论文中的类别、样本规模、评估口径对齐后，才能严谨地谈“是否优于论文方法”。

## 正在推进的下一步

截至 **2026 年 6 月 7 日**，下一步重点是：

1. 完成 `cold_test_augmented_10` 的正式编辑任务；
2. 生成对应的 `deltaW` 文件；
3. 用相同评估口径回灌推荐指标；
4. 把 `baseline / micro10 / aug10` 放到同一张表里比较；
5. 再决定后续应该继续扩大实验，还是把项目定位为“结果审慎但闭环完整”的研究工程案例。

如果实验日志已经落盘，也可以使用仓库内的 `gredit-summarize-results` 命令自动抽取 `iid_ratio@10` 与 `ndcg@10`，避免继续手工整理结果表。
如果日志仍在 `184` 服务器上，可以直接运行 `gredit-sync-server184-results`，把远端日志同步到本地并重建最新结果表。
如果想快速得到可直接写进汇报或 README 的一句话结论，可以再运行 `gredit-build-experiment-summary` 生成最新摘要。
如果正式实验还在运行中，可以运行 `gredit-sync-server184-runtime` 把最新运行状态同步到本地文档。
如果想一步完成这两件事，可以直接运行 `gredit-refresh-latest-reporting`。
如果 latest 文档刷新后需要立即公开发布，可以再运行 `gredit-publish-latest-reporting --push-remote agent-rec --push-remote origin`。

## 对外阅读建议

如果你是第一次看这个项目，建议按以下顺序理解：

1. 先看 [README](../README.md)，理解项目目标和整体流程；
2. 再看 [data_preparation.md](./data_preparation.md)，理解编辑请求是怎么构造出来的；
3. 最后看本文档，快速判断实验目前推进到了哪一步。

这样可以把“项目结构”和“实验状态”分开理解，不会把公开仓库误看成已经拿到最终正结果的成品论文复现。
