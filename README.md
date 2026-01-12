# **Title: Discipline over Praise: Optimizing Reasoning Traces in Gemma-3 1B via Failure-Aware GRPO**

## **Subtitle: A Hierarchical Reward Approach to Mitigate Logical Collapse and Enhance Commitment in Small Language Models**

### **Track: Math & Logical Reasoning**

---

## **1. Overview**

While large-scale models exhibit impressive reasoning, small-scale models (around 1B parameters) often struggle to maintain consistent reasoning traces, frequently falling into infinite loops or abandoning the task. This project utilizes **Tunix**, Google’s JAX-native library, to post-train **Gemma-3 1B** using Group Relative Policy Optimization (GRPO). We introduce a "Hierarchical Discipline" framework, demonstrating that small models are optimized more effectively by strictly penalizing failure patterns than by merely rewarding correct answers.

---

## **2. Methodology & Training Strategy**

### **2.1 Training Infrastructure**

* **Library:** Tunix (JAX-native)
* **Model:** Gemma-3 1B
* **Hardware:** Colab TPU VM v3-8 session
* **Dataset:** GSM8K (English-only)

### **2.2 Hierarchical Reward Design**

We transitioned through six reward configurations to identify the optimal balance between format adherence and logical integrity:

1. **Logiconly:** Baseline correctness (`check_answer`).
2. **GRPO-FT:** Enforcement of XML structures (`<reasoning>`, `<answer>`).
3. **Step-Logic:** Encouraging logical connectors (e.g., "Therefore", "Step 1").
4. **Discipline (Core):** Introduction of `penalty_failure_like` to punish non-responses and evasive logic.
5. **Discipline 2 / Full-Aware:** Advanced auditing for unit consistency and numerical coverage.

### **2.3 The "Discipline" Philosophy**

Our core hypothesis is that **small models lack "stopping ability" rather than "calculation ability."** We implemented aggressive negative rewards to block "easy exits":

* **Answer Missing Penalty (-3.0):** Severe punishment for failing to provide a final numerical answer.
* **Stagnation Penalty (-0.75):** Penalizing repetitive reasoning loops with zero information gain.

---

## **3. Detailed Performance Analysis**

The transition to the **Discipline** set marked a significant breakthrough in model reliability.

| Set | Acc (%) | Format (%) | Failure (%) | Missing (%) |
| :--- | :---: | :---: | :---: | :---: |
| Baseline | 45.31 | 1.56 | 20.31 | 20.31 |
| logiconly | 43.75 | 3.13 | — | — |
| grpoft | 45.31 | 7.81 | — | — |
| steplogic | 48.44 | 9.38 | — | — |
| **discipline** | **53.13** | 1.56 | **12.50** | **10.94** |
| full-aware | 48.44 | **12.50** | 15.63 | 14.06 |

### **Key Insights:**

* **Commitment:** By penalizing missing answers, the "Missing Rate" halved (20% → 11%). The model was forced to commit to a conclusion, raising Accuracy to its peak of **53.13%**.
* **The Format Trade-off:** While "Full-Aware" maximized format compliance (12.5%), Accuracy dipped. This suggests that for 1B models, simultaneous strict auditing of units and format creates a "cognitive overhead" that interferes with raw calculation.

---

## **4. Error Analysis: Case Study**

One illustrative failure involved a "Pencil Box" problem where the baseline model entered a loop, declaring information "unknown" despite it being present in the prompt.

### **Why "Discipline" Fixed This:**

* **Metacognition:** We rewarded tokens like "Wait" or "Actually." This encouraged the model to pause and recalculate when it detected a contradiction, rather than hallucinating "unknown" variables.
* **Auditing:** `penalize_false_unknowns` ensured that if numerical data exists in the prompt, the model is penalized for claiming it is missing.

---

## **5. Conclusion & Future Work**

The experiment proves that for small-scale models like Gemma-3 1B, **Discipline is more effective than Praise.** Restricting the search space by defining "what not to do" allows the model to find the correct reasoning path more efficiently within limited compute constraints.

**Future Directions:**

* **Dynamic Weighting:** Implementing a curriculum where format constraints are introduced only after the model masters the reasoning discipline.
* **Semantic Auditing:** Moving beyond regex-based rewards to LLM-as-a-judge rewards within the Tunix pipeline to detect "Semantic Flips" (e.g., confusing "failed" with "remained").

---

## **6. Attached Resources**

Notebook: [Link to Public Kaggle Notebook]

