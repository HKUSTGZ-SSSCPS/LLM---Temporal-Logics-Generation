




| Rule                           | Premise φp                                                   | Conclusion φc                                                |
| ------------------------------ | ------------------------------------------------------------ | ------------------------------------------------------------ |
| no right passing               | ¬div-lane(i) ^ ¬acc-lane(i) ^ ¬dense(i) ^ ¬built-up ∨ motorway(i) | ¬(behind(i→j) ^ X（behind(i→j) U right(i→j) U in-front(i→j))) |
| safe lane change               | lane-change                                                  | sd-rear                                                      |
| speed advantage for overtaking | behind (i→j) ^ ⭕(behind (i→j) U left(i→j) U in-front(i→j))   | speed-adv (i→j) U in-front(i→j)                              |
| safe distance (preced.)        | T                                                            | sd-front                                                     |
| being overtaken                | right(i→j) ^ near (i→j)                                      | ¬acc(i)                                                      |
| zipper merge                   | φzip-sit ^ pred(i→j) ^ ¬merged(i) ^ (pred(i→j) ∨ merged(j)) U merged(i) | (merged(i) ^ merged(j) ⇒ ¬pred(i→j))                         |



(¬div-lane(i) & ¬acc-lane(i) & ¬dense(i) & ¬built-up | motorway(i)) -> (¬(behind(i -> j) & X(behind(i->j) U right(i->j) U in-front(i->j))))

lane-change -> sd-rear

(behind (i->j) & X(behind (i->j) U left(i->j) U in-front(i->j))) -> (speed-adv (i->j) U in-front(i->j))

T -> sd-front

(right(i->j) & near (i->j))-> ¬acc(i)

(zip-sit & pred(i->j) & ¬merged(i) & (pred(i->j) | merged(j)) U merged(i)) -> (G(merged(i) & merged(j) <-> ¬pred(i->j)))





**保持控制**：驾驶员只能以能够始终控制车辆的速度行驶。

- LTL表达式：`G (speed ≤ control_limit)`

**不低于最低速度**：在没有充分理由的情况下，不得以妨碍交通流的速度行驶。

- LTL表达式：`G ((speed < min_speed) → good_reason)`

**遵守速度限制**：遵守“最大允许速度”。

- LTL表达式：`G (speed ≤ speed_limit)`

**禁止停车**：在高速公路和机动车道路上，禁止停车，包括路肩。

- LTL表达式：`G ((location ≠ motorway) ∨ ¬stop)`

**右侧行驶**：尽可能靠右行驶。

- LTL表达式：`G (lane_position ≤ rightmost_lane)`

**超车**：只有在自车速度明显高于被超车辆时才允许超车。

- LTL表达式：`G (overtaking → (speed_advantage > threshold))`

**保持安全距离**：驾驶员必须与前车保持足够的安全距离。

- LTL表达式：`G (distance_to_predecessor ≥ safe_distance)`

**被超车时不加速**：被超车辆不得增加速度。

- LTL表达式：`G (being_overtaken → ¬accelerating)`

**拉链式并线**：在多车道道路上，如果一条车道的连续行驶不可能，或者车道即将结束，相邻车道的车辆必须允许其他车道的车辆在道路变窄前立即换道，以交替拉链式加入其车流。

- LTL表达式：`G (zipper_merge_condition → zipper_merge_behavior)`