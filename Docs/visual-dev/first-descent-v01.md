# 第一眼深井 · 视觉草案 v01

> 历史记录（2026-09-10）：以下内容记录当时的样片、实现与评价。当前美术目标见[最新规范](../ArtDirection/art-direction-v1.md)；本文旧工业主导、检修工外观或永夜要求不再作为后续制作标准，原有测试与实现状态仍按原日期理解。

- 日期：2026-09-05
- 状态：用户评价“还不错啊”，同意沿该方向推进可走动 3D 灰盒，作为首个样段的视觉参考；尚非整款游戏的最终美术规范。
- 工具：内置 image_gen。
- 原图：[first-descent-v01.png](../../assets/concepts/first-descent-v01.png)
- 性质：生成的概念图，用于视觉讨论；不是实际游戏截图或已完成的 3D 场景。

## 本轮目标

用户希望通过小步、可见的成果获得开发动力。本轮仅交付一张第三人称探索视角概念图，检验“震撼、压抑、沉浸”的视觉方向，后续根据反馈推进。

## 画面事件

两名远征者离开狭窄矿道，来到深渊边缘的栈道。同伴抬手示意停步，前方巨大的地下工业遗迹中出现灯光。

## 初步观察

- 已表现出工业遗迹、冷暖光源、深渊纵深和可辨识的栈道。
- 人物与巨型立柱形成尺度参照，同伴动作提供叙事情境。
- 人物占画面比例大于原提示词目标，实际镜头距离和关卡尺寸需要在灰盒中验证。
- 静态图不能验证走动时的路线连续性、碰撞、真实灯光效果或性能。
- 后续：进入小型 3D 空间样段，暂不批量扩展概念图或制作正式角色模型。

## 完整生成提示词

```text
Use case: stylized-concept
Asset type: one cinematic environment concept frame for the original game 灰烬深井 (Ash Well), first playable third-person exploration visual target. A SINGLE widescreen 16:9 image, preferably 2048x1152. No contact sheet.

Primary request: The first moment a small expedition steps out of a narrow mine tunnel and discovers an impossibly vast buried industrial civilization. The emotional priorities are overwhelming awe, oppressive silence, believable physical presence, and a compelling urge to walk further. Mature photorealistic game environment concept art with exceptionally coherent architectural scale and composition.

Composition/framing: Actual playable third-person camera at human shoulder height, about 3 meters behind the protagonist, 32mm equivalent lens. Show the protagonist's entire back-facing body in the lower-left third, about 25% of frame height. Their boots visibly contact the same walkable stone-and-metal service ledge that starts in the immediate foreground, curves toward the middle distance, and reaches a distant access door. This route must remain visibly continuous and wide enough for people; plausible railings and structural supports. A second expedition member stands several meters ahead, small enough not to block the view, holding up a hand to halt the player and turning a lowered lantern toward the abyss. Two people total.

Scene/backdrop: A tight rough mine opening, rusty steel bracing, frayed cables and dripping pipes frame the near edges. Beyond the opening is an underground void hundreds of meters high. Across it stands a buried monumental civic structure, a cathedral-like industrial transit hall built by a lost civilization: immense layered stone arches, concrete ribs, oxidized iron buttresses, enormous silent machinery integrated into its foundations. Tiers of tiny apartments, maintenance doors, bridges, stairs and loading platforms make its immense scale legible. One colossal structural pier alone dwarfs the entire human expedition. The architecture disappears above into a fully enclosed cavern ceiling and below into deep fog. No sky, no sun, no ordinary medieval castle, no floating structures. The distant structure should look constructed and inhabitable, not like a random mass of ornamental shapes.

Visual event: A thin, incomplete chain of faint amber windows has just begun to light up deep inside the apparently abandoned building, drawing the player's eye across the abyss. Its purpose and inhabitants remain unknown. Nothing attacks. The companion's stopping gesture makes the event feel consequential.

Character design: Original exhausted expedition workers, functional layered charcoal canvas coats, compact oxygen/filter pack, worn steel shoulder protection, sturdy gloves and boots, practical tool belt. Protagonist carries a modest warm ember lantern low in one hand. No glamorous armor, capes, glowing swords, oversized guns, recognizable franchise characters or logos.

Lighting/mood: Very dark but fully readable. Broad, dim slate-blue ambient bounce and suspended mineral haze separate at least five layers of depth; localized amber lanterns gently illuminate glove leather, wet stone, rusty railing and the edge of the protagonist's silhouette. Foreground intimate warmth occupies only a small area against the colossal cold distance. Preserve rich midtones, convincing reflections and nuanced material texture. Heavy quiet, damp cold air, volumetric atmosphere, restrained color. Avoid crushed blacks, overexposed lights, teal-orange blockbuster excess, horror jump scares or visible monsters.

Materials/textures: Weathered masonry, wet concrete, oxidized riveted steel, ash sediment, old electrical insulators, repaired expedition garments. Architectural systems share a coherent old-industrial design language; no excessive generic pipes.
Text: none. No UI, no titles, no labels, no watermark.
This is a concept illustration to establish a visual target, not a claim of an existing rendered game.
```
