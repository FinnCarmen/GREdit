# GREdit

GREdit 是一个面向**冷启动生成式推荐**的模型编辑项目。它围绕 TIGER 生成式推荐器构建，目标不是做一个轻量工具库，而是把一条完整、可复现、可解释的研究与工程链路整理成公开项目：

1. 先训练基础生成式推荐模型；
2. 再构造冷启动编辑请求；
3. 然后求解模型编辑参数更新；
4. 最后回到推荐任务上验证编辑后的效果。

如果把这个项目放在公开主页上，我希望它传达出的信号很明确：这不是只会“跑通一个脚本”的实验代码，而是一个把**问题定义、数据构造、训练入口、编辑过程、评估回路**都打包清楚的研究工程项目。

## 项目在做什么

传统推荐系统里的模型编辑，更多出现在参数量较小、目标较单一的设定里。GREdit 关注的是另一类问题：当推荐器本身已经是生成式模型时，能不能在不重新完整训练的前提下，对模型注入新的冷启动知识，并尽量保持原有推荐能力。

这个仓库对应的是一条 TIGER-based 的实现路径，核心包含三部分：

- `genrec/`：生成式推荐主干，包括数据集、模型、训练与评估流程；
- `genrecedit/`：GenRecEdit 的编辑算法实现，包括超参数、协方差缓存、模型封装与编辑入口；
- `prepare_edit_data.py`：把原始推荐数据和缓存特征整理成可编辑请求的脚本。

从公开展示角度看，这个项目的价值主要在三点：

- 它把“模型编辑”真正落到了“生成式推荐”这个具体任务上；
- 它不仅有算法代码，也有数据准备与复现实验入口；
- 它保留了研究项目该有的工程结构，而不是把所有逻辑塞进 notebook。

## 仓库结构

```text
GREdit/
├── README.md
├── CITATION.cff
├── pyproject.toml
├── requirements.txt
├── rec_main.py
├── edit_main.py
├── prepare_edit_data.py
├── Scripts/
│   ├── rec_train.sh
│   ├── prepare_data.sh
│   └── edit.sh
├── docs/
│   └── data_preparation.md
├── data/
│   ├── README.md
│   ├── ckpt/
│   └── Edit/
├── genrec/
├── genrecedit/
├── util/
└── notebooks/
```

各部分职责可以概括为：

- `rec_main.py`：基础推荐模型训练与评估入口；
- `edit_main.py`：模型编辑入口；
- `prepare_edit_data.py`：编辑请求构造入口；
- `Scripts/`：对完整流程做了一层可直接执行的封装；
- `docs/`：补充解释数据准备与目录约定；
- `notebooks/`：保留原始研究过程中的探索记录。

## 适合谁看这个项目

这个仓库主要适合三类读者：

- 对推荐系统感兴趣，想看生成式推荐如何接入模型编辑的人；
- 对研究工程化感兴趣，想看一个项目如何从实验代码整理为可公开仓库的人；
- 面试或学术交流场景下，希望快速判断“作者是否真的做过完整闭环”的读者。

如果你是面试官，我建议重点看三处：

1. `prepare_edit_data.py`
   这里体现了我如何把研究想法变成稳定的数据构造流程。
2. `genrecedit/`
   这里是项目的方法主体，体现了编辑算法与模型封装方式。
3. `Scripts/`
   这里体现了我是否考虑过复现路径、参数入口和多阶段串联。

## 环境安装

### 方式一：按原始实验环境安装

```bash
conda create -n gredit python=3.10 -y
conda activate gredit
python -m pip install --upgrade pip
pip install -r requirements.txt
```

这条路径最接近我打包这个项目时使用的环境，`requirements.txt` 中已经包含 PyTorch CUDA 12.4 相关索引配置。

### 方式二：作为 Python 项目安装

如果你更习惯可编辑安装和命令行入口，可以使用：

```bash
conda create -n gredit python=3.10 -y
conda activate gredit
python -m pip install --upgrade pip
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu124
pip install -e .
```

安装后可用的命令包括：

- `gredit-train`
- `gredit-prepare`
- `gredit-edit`

## 当前支持的类别

目前公开整理过、并在目录结构中直接体现的类别有：

- `Video_Games`
- `Cell_Phones_and_Accessories`
- `Software`

`prepare_edit_data.py` 中还保留了其他 Amazon Reviews 2023 类别的一些默认配置，但公开版仓库主要围绕上述三个类别组织示例与脚本。

## 数据目录约定

仓库默认采用以下目录布局：

```text
data/
├── ckpt/
│   └── TIGER_<category>/
│       └── genrec_default_ori.pth
├── cache/
│   └── AmazonReviews2023/
│       └── <category>/
│           └── processed/
│               └── sentence-t5-base.sent_emb
└── Edit/
    └── <category>/
        ├── edit_requests_COV.json
        └── edit_requests_cold_test_augmented_<n>.json
```

这里需要特别说明三点：

- 仓库**不直接附带**真实的预训练权重；
- 仓库**不直接附带**完整的处理后缓存；
- `data/` 下保留的同名文件，很多只是为了说明路径结构的占位文件。

也就是说，这个公开仓库的重点是**代码、流程和组织方式**，不是把大体积实验产物一股脑塞进 GitHub。

详细说明见 [data/README.md](data/README.md)。

## 一条完整的运行流程

### 第一步：训练基础推荐模型

训练某个类别的 TIGER 模型：

```bash
bash Scripts/rec_train.sh Video_Games
```

或者使用安装后的命令行入口：

```bash
gredit-train --model TIGER --category Video_Games --max_rows 0.5
```

训练完成后，后续流程默认会读取：

```text
data/ckpt/TIGER_Video_Games/genrec_default_ori.pth
```

脚本中预设的 `max_rows` 为：

- `Video_Games`：`0.5`
- `Cell_Phones_and_Accessories`：`0.1`
- `Software`：`0.5`

这个设计本质上是在复现成本与实验规模之间做折中，方便快速重跑而不必每次都拉满数据。

### 第二步：构造编辑请求

生成协方差样本和冷启动增强编辑请求：

```bash
bash Scripts/prepare_data.sh Video_Games
```

或者直接执行：

```bash
gredit-prepare \
  --category Video_Games \
  --number_per_item 10 \
  --topk 10 \
  --cache_dir data/cache/ \
  --output_dir data/Edit/Video_Games
```

这一阶段会生成：

- `data/Edit/<category>/edit_requests_COV.json`
- `data/Edit/<category>/edit_requests_cold_test_augmented_<number_per_item>.json`

从逻辑上看，这一步做了几件事：

1. 读取 TIGER 已处理好的数据切分；
2. 把训练样本转成协方差估计所需的请求格式；
3. 找到目标测试切分中的冷启动物品；
4. 读取 `sentence-t5-base.sent_emb` 做相似物品检索；
5. 用相似训练物品替换历史位置，构造增强编辑样本；
6. 再把这些样本编码成 GenRecEdit 使用的 JSON 请求。

生成后的请求条目包含：

- `history`：推荐上下文的 token 序列；
- `target_sids`：目标物品的语义 ID；
- `case_id`：样本编号。

### 第三步：执行编辑并回到推荐任务验证

执行编辑流程：

```bash
bash Scripts/edit.sh Video_Games
```

当前公开脚本默认使用：

- `EDIT_POSTFIXES=(cold_test_augmented)`
- `COV_LAMBDAS=(1000)`
- `NUMBER_KNOWLEDGES=(10)`
- `POS2LAYER=(0 1 2 3)`

如果想从外部覆盖超参数，可以这样传：

```bash
CUDA_VISIBLE_DEVICES=0 \
COV_LAMBDAS="1000 3000" \
NUMBER_KNOWLEDGES="5 10" \
POS2LAYER="0 1 2 3" \
bash Scripts/edit.sh Video_Games
```

这一阶段会读取：

- `data/ckpt/TIGER_<category>/genrec_default_ori.pth`
- `data/Edit/<category>/edit_requests_COV.json`
- `data/Edit/<category>/edit_requests_cold_test_augmented_<n>.json`

并输出：

```text
results/<category>/deltaW_edit_requests_cold_test_augmented_<cov_lambda>_<n>.pt
```

随后脚本会重新加载基础模型、应用 `deltaW`，再回到推荐评估流程中查看编辑效果。

这也是我认为这个项目最像“完整工程闭环”的地方：编辑不是停留在一个中间结果文件上，而是要回到最终任务上接受检验。

## 命令行入口说明

### `rec_main.py`

基础训练与评估入口：

```bash
python rec_main.py --model TIGER --category Video_Games --max_rows 0.5
```

这个脚本会把未显式解析的参数继续传给 GenRec 的配置解析逻辑，因此适合做模型参数扩展或批量实验。

### `prepare_edit_data.py`

常用参数包括：

- `--category`
- `--cache_dir`
- `--output_dir`
- `--pretrained_model_path`
- `--max_rows`
- `--topk`
- `--number_per_item`
- `--augmented_split`
- `--seed`
- `--no_write_cov`
- `--no_write_augmented`
- `--save_tokenized_augmented`

示例：

```bash
python prepare_edit_data.py \
  --category Cell_Phones_and_Accessories \
  --topk 10 \
  --number_per_item 10 \
  --augmented_split cold_test \
  --cache_dir data/cache/ \
  --output_dir data/Edit/Cell_Phones_and_Accessories
```

### `edit_main.py`

常用参数包括：

- `--model_name`
- `--pretrained_model_path`
- `--covariance_data_file`
- `--edit_requests_file`
- `--edit_name`
- `--category`
- `--cov_lambda`
- `--number_knowledge`
- `--pos2layer`
- `--cache_dir`
- `--output_dir`

示例：

```bash
python edit_main.py \
  --category Video_Games \
  --pretrained_model_path data/ckpt/TIGER_Video_Games/genrec_default_ori.pth \
  --covariance_data_file data/Edit/Video_Games/edit_requests_COV.json \
  --edit_requests_file data/Edit/Video_Games/edit_requests_cold_test_augmented_10.json \
  --edit_name edit_requests_cold_test_augmented \
  --cov_lambda 1000 \
  --number_knowledge 10 \
  --pos2layer 0 1 2 3
```

## 工程化整理时做过的处理

这个公开版不是简单把本地代码打包上传，而是做过一轮面向公开阅读的整理，主要包括：

- 增加 `pyproject.toml`，支持 `pip install -e .`；
- 补齐 `genrec/__init__.py`，让包结构更完整；
- 修正训练脚本入口，使其直接调用 `rec_main.py`；
- 让 `prepare_data.sh` 和 `edit.sh` 支持通过参数或环境变量切换类别与超参数；
- 保留 `data/` 目录形状，但把无法公开分发的大文件替换为占位文件说明。

这部分整理本身也体现了一种工程判断：公开仓库最重要的是**可理解、可安装、可定位、可继续开发**，而不是把所有历史产物原样搬上来。

## 输出内容

典型输出包括：

```text
data/ckpt/TIGER_<category>/genrec_default_ori.pth
data/Edit/<category>/edit_requests_COV.json
data/Edit/<category>/edit_requests_cold_test_augmented_<n>.json
results/<category>/deltaW_*.pt
outputs/logs/
outputs/tensorboard/
```

其中 `results/` 和 `outputs/` 已加入忽略规则，不会作为仓库的一部分提交。

## 可能遇到的问题

### 找不到 `genrec_default_ori.pth`

说明基础推荐模型尚未训练完成，或者权重没有放到约定路径下。需要先完成训练，或手动将 checkpoint 放到：

```text
data/ckpt/TIGER_<category>/genrec_default_ori.pth
```

### 缺少 `sentence-t5-base.sent_emb`

说明处理后的缓存不完整。至少需要补齐：

```text
data/cache/AmazonReviews2023/<category>/processed/sentence-t5-base.sent_emb
```

### 脚本只跑了一个类别

可以直接把类别作为参数传入：

```bash
bash Scripts/prepare_data.sh Video_Games Software
bash Scripts/edit.sh Video_Games
```

或者提前设置：

```bash
export CATEGORIES="Video_Games Software"
```

### CUDA 显存不足

可以从三处入手：

- 调小模型相关 batch 配置；
- 调低类别采样比例；
- 更换显存更大的 GPU。

### `pip install -e .` 时 PyTorch 版本不匹配

优先按官方 CUDA wheel 方式先装好 PyTorch，再执行：

```bash
pip install -e .
```

## 项目边界与说明

这个仓库仍然保留了研究项目的一些特征，因此有几个边界需要说明：

- 它首先是研究代码，其次才是通用工具库；
- 主要公开的是 TIGER-based 的一条复现链路；
- notebook 被保留下来，是为了保留研究轨迹，不代表它们是最推荐的使用入口；
- 大模型权重、缓存与大体积编辑产物不在这个公开仓库中分发。

如果你把这个项目当作简历或主页项目来看，我更希望它被理解为：**我不仅做了方法，还把方法放进了一个别人可以读懂、装起来、接着跑的工程骨架里。**

## 引用

如果这个项目对你的研究有帮助，可以引用：

```bibtex
@article{shen2026bringing,
  title={Bringing Model Editing to Generative Recommendation in Cold-Start Scenarios},
  author={Shen, Chenglei and Shi, Teng and Yu, Weijie and Zhang, Xiao and Xu, Jun},
  journal={arXiv preprint arXiv:2603.14259},
  year={2026}
}
```
