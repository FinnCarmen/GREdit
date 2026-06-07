# 数据准备说明

这一页专门解释 GREdit 中“编辑请求是怎么来的”。

对这个项目而言，数据准备不是附属工作，而是方法成立的重要一环。因为模型编辑的输入并不是原始推荐样本本身，而是一组经过筛选、变换和重新编码后的编辑请求。如果这一步做得不清楚，后面的编辑结果就很难解释。

## 本仓库中会用到哪些文件

以 `Cell_Phones_and_Accessories` 为例，打包后的实验流程默认会读取两类请求文件：

- `data/Edit/Cell_Phones_and_Accessories/edit_requests_COV.json`
- `data/Edit/Cell_Phones_and_Accessories/edit_requests_cold_test_augmented_10.json`

其中：

- `edit_requests_COV.json` 用于协方差统计；
- `edit_requests_cold_test_augmented_10.json` 用于真正执行编辑。

## notebook 和脚本的关系

仓库中保留了两份早期 notebook：

- `notebooks/数据划分_covdata.ipynb`
- `notebooks/数据划分_train.ipynb`

它们主要是研究探索过程的记录。为了把流程整理成更稳定、可复现、适合公开仓库使用的形式，我把核心逻辑收敛到了下面两个入口：

- `prepare_edit_data.py`
- `Scripts/prepare_data.sh`

也就是说，公开使用时应优先使用脚本，而不是依赖 notebook 手动运行。

## 两类请求文件各自表示什么

### 1. `edit_requests_COV.json`

这个文件来自**训练集 token 化结果**，主要用于 GenRecEdit 中的协方差估计。可以把它理解为：编辑算法在求解参数更新时，需要一组“背景统计样本”，这个文件就是这组样本的标准化表示。

### 2. `edit_requests_cold_test_augmented_10.json`

这个文件对应真正的冷启动编辑请求。它不是简单从测试集直接导出的，而是经过了“相似物品检索 + 序列替换 + 重新编码”的处理。

其大致流程是：

1. 读取指定类别的 Amazon Reviews 2023 数据切分；
2. 找到目标切分中的冷启动物品；
3. 读取 `sentence-t5-base.sent_emb` 中的物品向量；
4. 用余弦相似度在训练物品中寻找相似项；
5. 在训练序列里用目标冷启动物品替换相似位置，构造增强样本；
6. 用 TIGER tokenizer 对增强样本重新编码；
7. 生成 GenRecEdit 所需的 JSON 请求格式。

最终每条请求会包含：

- `history`：输入历史序列；
- `target_sids`：目标语义 ID；
- `case_id`：样本编号。

## 如何运行

最直接的方式是：

```bash
bash Scripts/prepare_data.sh
```

如果想显式指定类别，可以写成：

```bash
bash Scripts/prepare_data.sh Cell_Phones_and_Accessories
```

也可以直接调用 Python 脚本：

```bash
python prepare_edit_data.py \
  --category Cell_Phones_and_Accessories \
  --number_per_item 10 \
  --topk 10 \
  --cache_dir data/cache/ \
  --output_dir data/Edit/Cell_Phones_and_Accessories
```

## 运行前必须准备好的输入

脚本默认假设以下处理后缓存已经存在：

```text
data/cache/AmazonReviews2023/Cell_Phones_and_Accessories/processed/
```

其中最关键的是：

```text
sentence-t5-base.sent_emb
```

这个文件用于相似物品检索。如果它不存在，增强编辑样本就无法构造。

因此可以把前置条件概括为两项：

- 已经有 TIGER 训练/预处理阶段生成的缓存；
- 已经能从本地缓存或 HuggingFace 正常读取 Amazon Reviews 2023 数据。

## 为什么要把这一步单独写成脚本

从工程视角看，这一步单独脚本化有三个好处：

- 避免 notebook 中常见的硬编码路径与手动状态污染；
- 让请求构造可以作为独立阶段重复执行；
- 方便把实验设置转成明确的命令行参数。

从公开项目视角看，这一步也能体现项目是否“讲得清楚”。很多研究代码的问题不在于模型本身，而在于数据准备依赖隐藏得太深，外部读者几乎无法判断实验输入是如何形成的。GREdit 这部分文档和脚本，就是为了把这个过程显式化。
