# 静态质检打回清单 —— 执行结果

## 本次打回（按做题人分组）

### 唐璐（3 道）

| 飞书序号 | 题号 | 题目 | 当前状态 | 理由来源 | 打回原因 | 执行结果 |
| --- | --- | --- | --- | --- | --- | --- |
| 140 | #435 | 批量导入清单 | 待返修 | 质检备注 | 静态不通过<br>1 批量导入的核心目标和机制已由公开 Issue/PR 覆盖：Issue 提出文件清单及单次 state/lock 生命周期，两个 PR 补充文件或 stdin、JSON 清单和一次命令导入多组地址/ID：https://github.com/hashicorp/terraform/issues/22219；https://github.com/hashicorp/terraform/pull/22227；https://github.com/hashicorp/terraform/pull/23926<br>2 验收标准额外强制机器可读 JSON 结果，但原始需求只要求逐条输出结果 | 已打回 |
| 145 | #448 | URI 请求目标规范化与代理转发策略 | 待返修 | 质检备注 | 静态不通过<br>1 公开 Issue 已描述经代理错误发送 origin-form 并要求 absolute URI；对应 PR 实现 FullURI，维护者还明确建议用字段选择代理形式并保留直连兼容。题目的观察钩子、重定向复用和错误校验是同一方案的常规扩写：https://github.com/valyala/fasthttp/issues/239；https://github.com/valyala/fasthttp/pull/240 | 已打回 |
| 164 | #468 | 批量 TTL 诊断 | 待返修 | 质检备注 | 静态不通过<br>1 Rubric 新增了 Prompt 未要求的 GrantedTTL 返回字段和“空 lease 集合诊断全部可见 lease”语义，扩大了公开行为范围 | 已打回 |

### 帅先伟（3 道）

| 飞书序号 | 题号 | 题目 | 当前状态 | 理由来源 | 打回原因 | 执行结果 |
| --- | --- | --- | --- | --- | --- | --- |
| 98 | #385 | caddy-01 | 待返修 | 质检备注 | 静态不通过<br>1 产物结果把 TCP 回复包含期望串判为通过，补丁也使用子串包含匹配；但 Prompt 与 Rubric 要求读到的首段回复与期望串一致，验收结论与需求语义不一致 | 已打回 |
| 99 | #386 | caddy-05 | 待返修 | 质检备注 | 静态不通过<br>1 Rubric 对 request_body 的 max_size、set 与压缩叠加只要求顺序语义明确，未给出应采用的顺序或可观察结果；同时未覆盖已带 Content-Encoding 的请求体不得再次改写这一关键兼容性反例，无法阻止不符合 Prompt 的实现通过 | 已打回 |
| 100 | #388 | caddy-03 | 待返修 | 质检备注 | 静态不通过<br>1 实际有效轮数为 59（不超过 100），完成状态为“完成”<br>2 第 5 项把非法配置导致整体配置加载失败与不影响其他上游建连合并为同一验收条件，按 Caddy 整体配置加载语义无法同时从外部观察；同时 Prompt 明确要求同一上游被多个代理块引用时各自独立建连，但验收项未覆盖该边界<br>3 产物结果把第 5 项标为通过，却同时注明“不影响其他上游建连”仅在对象级成立，与该项字面验收及整体“完成”状态不一致 | 已打回 |


### 杨国威（2 道）

| 飞书序号 | 题号 | 题目 | 当前状态 | 理由来源 | 打回原因 | 执行结果 |
| --- | --- | --- | --- | --- | --- | --- |
| 76 | #363 | PermutationGroup完整双陪集分解与规范代表元 | 待返修 | 质检备注 | 静态不通过<br>1 题目由公开的通用双陪集接口、SymPy 既有双陪集规范代表算法和公开性能问题合成；组合后已覆盖核心目标、代表元与大小接口、基于稳定子链的字典序规范化机制及大置换群性能边界，未发现独立于这些来源的实质性核心需求。<br>https://docs.gap-system.org/doc/ref/chap39.html#X78B98B257E981046<br>https://docs.sympy.org/latest/modules/combinatorics/tensor_can.html#sympy.combinatorics.tensor_can.double_coset_can_rep<br>https://github.com/gap-system/gap/issues/6047 | 已打回 |
| 85 | #375 | DomainMatrix完整移位Popov逼近基 | 待返修 | 质检备注 | 静态不通过<br>1 题目是 SageMath 已公开 minimal_approximant_basis 能力向 SymPy DomainMatrix 的改写与 API 适配；公开文档已覆盖完整逼近模基、逐列阶数、整数 shift、行式计算、移位 Popov 规范形、完整性验证、零/负阶约束和维度错误，题目新增内容主要是目标类适配及常规域/表示边界。<br>https://doc.sagemath.org/html/en/reference/matrices/sage/matrix/matrix_polynomial_dense.html#sage.matrix.matrix_polynomial_dense.Matrix_polynomial_dense.minimal_approximant_basis<br>https://doc.sagemath.org/html/en/reference/matrices/sage/matrix/matrix_polynomial_dense.html#sage.matrix.matrix_polynomial_dense.Matrix_polynomial_dense.is_minimal_approximant_basis<br>https://github.com/sagemath/sage/issues/35258<br>https://github.com/sagemath/sage/issues/39587 | 已打回 |


### 王乙文（1 道）

| 飞书序号 | 题号 | 题目 | 当前状态 | 理由来源 | 打回原因 | 执行结果 |
| --- | --- | --- | --- | --- | --- | --- |
| 57 | #340 | SQLAlchemy ORM loader-plan 缓存代际隔离 | 待返修 | 质检备注 | 静态不通过<br>1 最新版交付包与当前记录不一致：task.toml 中的 realism_and_difficulty 仍是概括性旧文本，未包含当前记录新增的基线复现与限制说明<br>2 固定基线中不存在 Prompt 所称可跨 registry 复用或迟到提交的 loader-plan 缓存。现有加载策略绑定于映射属性，registry.dispose() 会拆除所属 mapper；补丁新建 _loader_plan.py 缓存子系统后再包装既有加载路径，未闭合题述现有故障的真实触发链。当前记录的真实性说明也明确未复现跨 registry 错误共享或迟到提交 | 已打回 |

### 赵小平（1 道）

| 飞书序号 | 题号 | 题目 | 当前状态 | 理由来源 | 打回原因 | 执行结果 |
| --- | --- | --- | --- | --- | --- | --- |
| 70 | #359 | 共享连接配额 | 待返修 | 质检备注 | 静态不通过<br>1 最新版交付包与当前记录不一致：task.submit_date、task.requirement_met、task.run_result 和 tests/nl_rubric.yaml 均不一致。当前记录称完成且 6 项全通过，包内 task.toml 为部分完成且第 3、4、5 项未通过<br>2 包内 Rubric 第 5 项新增完整只读统计快照、各 key 使用量、等待量，以及跨线程和多事件循环契约；这些是独立的可观测性和并发 API 要求，超出 Prompt 的共享配额、拒绝响应及生命周期归还范围<br>3 当前记录有效轮数为 59（≤100），完成状态为完成，且 Type 标注效果好，不符合轮数与完成度规则<br>4 当前记录写明任务已完成且六项产物结果全部通过，但最新版交付包写明部分完成，并记录第 3、4、5 项失败，完成度与产物结果无法互相印证 | 已打回 |

