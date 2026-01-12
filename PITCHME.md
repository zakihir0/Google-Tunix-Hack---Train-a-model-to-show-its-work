

⸻


# 実験報告書  
## 報酬関数セットの段階的導入による推論制御の検証

Gemma-3 1B + GRPO (Tunix)

---

## 実験の目的

**小規模LLM (Gemma-3 1B)** に対し、

> 正解報酬 → 推論規律 → Failure-aware 規律  

へ段階的に報酬を進化させることで  
**推論精度と一貫性がどう変化するか**を検証する。

---

## 実験の核心仮説

> 小規模モデルは  
> 「正解で報酬」より  
> 「失敗を禁止」した方が強くなる

---

## 報酬セットの設計思想

| フェーズ | 目的 |
|--------|------|
| logiconly | 正解を出す |
| grpoft | フォーマットを守る |
| steplogic | 推論を段階化 |
| discipline | 失敗を禁止 |
| failure-aware | 崩壊を防ぐ |

---

## 報酬セット一覧

| セット | 含まれる関数 |
|-------|-------------|
| **1 logiconly** | `check_answer`, `check_numbers` |
| **2 grpoft** | + `match_format_exactly`, `match_format_approximately` |
| **3 steplogic** | + `reward_step_logic`, `reward_self_correction` |
| **4 discipline** | + `penalty_failure_like` (基本) |
| **5 discipline2** | + 数値・単位・停滞ペナルティ |
| **6 full-aware** | 全Failure検知を最大感度で適用 |

---

## 評価指標

| 指標 | 意味 |
|------|------|
| Accuracy | 完全正解率 |
| Partial Acc | 部分正解率 |
| Format Acc | XML形式遵守率 |
| Failure Rate | 失敗構文率 |
| Answer Missing | 未回答率 |

---

## パフォーマンス比較

| Set | Acc | Partial | Format | Failure | Missing |
|-----|-----|--------|--------|---------|---------|
| Baseline | 45.3 | 46.9 | 1.5 | 20.3 | 20.3 |
| logiconly | 43.7 | 45.3 | 0.0 | 21.8 | 18.7 |
| grpoft | 45.3 | 46.8 | 1.5 | 20.3 | 20.3 |
| steplogic | 48.4 | 50.0 | 1.5 | 18.7 | 18.7 |
| discipline | **53.1** | 57.8 | 1.5 | 12.5 | **10.9** |
| discipline2 | 51.5 | 56.2 | **3.1** | **11.0** | 12.5 |
| full-aware | 53.1 | **58.0** | 1.5 | 12.5 | **10.9** |

---

## Phase 1  
### logiconly → grpoft

**何が起きたか**

* 正解率ほぼ不変
* Failure Rate ほぼ不変

**理由**

> 「答えさえ合えばOK」だと  
> 1Bモデルはショートカット（幻覚）を探す

---

## Phase 2  
### steplogic

**何が変わったか**

* Accuracy: 45.3 → 48.4
* Partial: 46.8 → 50.0

**なぜ？**

> 「first → then → therefore」  
> という **思考のリズム** を報酬化したため  
> 途中脱落が減少

---

## Phase 3  
### discipline → full-aware

**最大のジャンプ**

* Accuracy: **53.1%**
* Failure Rate: **20.3 → 12.5**
* Missing Answer: **20.3 → 10.9**

---

## 何が一番効いたか？

**最強の報酬**

Answer Missing  →  -3.0

> 「わからない」と言うより  
> 「不完全でも答えを出す」方が  
> 生存確率が高いと学習した

---

## Failure-aware がしたこと

| モデルの悪癖 | どう潰したか |
|-------------|--------------|
| 無限ループ | stagnation penalty |
| 言い訳 | failure_like |
| 数値無視 | missing_addends |
| 単位崩壊 | unit inconsistency |
| 無回答 | heavy penalty |

---

## 小規模LLMの本質

> **賢くするより  
> 馬鹿なことをできなくした方が強くなる**

---

## 結論

**1Bモデルに最も効いたのは**

> 正解への報酬ではなく  
> **失敗への規律（Discipline）**

Failure-aware RL は  
小型モデルを **推論可能な存在に変換する**

---

## 応用的含意

* CoT蒸留より Failure RL の方が効く
* 小型モデルは「禁止リスト」が必要
* 「考えさせる」より「壊させない」

---

## Appendix

使用した報酬関数の完全な Python 定義  
（別スライド or 別リポジトリ）


⸻
