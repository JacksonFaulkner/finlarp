// MATH tab node pages (ADD ... MATRIX x MATRIX), drawn in Blender through pbr3d in the
// picture-and-panel template. One overview per page, three beats each. The scenes are
// tools/pbr3d/blender/math_pages.py (built on math_kit.py) and play from assets/math_<slug>.glb.
//
// The arithmetic in every beat is worked by hand, not sourced: the numbers are the page's own
// worked examples (MATH_*.txt) and are checked by the tests below.

use super::blender::{self, Cell, BEAT_MS};
use super::Node;
use crate::ui::anim::{Beat, Scene};

macro_rules! math_page {
    ($build:ident, $cell:ident, $beats:ident, $slug:literal) => {
        static $cell: Cell = std::sync::OnceLock::new();
        fn $build() -> Box<dyn Scene> {
            blender::page(
                &$cell,
                include_bytes!(concat!("../../../../../tools/pbr3d/assets/math_", $slug, ".glb")),
                $beats,
            )
        }
    };
}

const ADD_BEATS: &[Beat] = &[
    Beat::new("3 dots and 4 dots: two amounts to combine", BEAT_MS)
        .note(
            "Two groups of dots sit in their trays: 3 red on the left, 4 blue on the right. Adding starts from these two amounts.",
            "3 red dots on the left tray, 4 blue dots on the right tray, and the centre tray empty",
        )
        .detail(
            "The answer depends only on how many dots there are, not on which tray they came from.",
            &["3 + 4 = 7", "Order does not change the sum: 4 + 3 is also 7"],
        ),
    Beat::new("put them in one tray: no dot is lost or made", BEAT_MS)
        .note(
            "The dots slide across into one shared tray. Moving them changes nothing about how many there are.",
            "the red and blue dots travelling to the centre tray while the side trays empty",
        )
        .detail(
            "Adding is counting the pile that results from putting two piles together.",
            &["3 dots + 4 dots = 7 dots in the combined tray"],
        ),
    Beat::new("count the pile: 3 + 4 = 7", BEAT_MS)
        .note(
            "All seven dots now sit in the centre tray. Counting them gives the sum.",
            "seven dots in the centre tray, three red and four blue, tagged 3 + 4 = 7",
        )
        .detail(
            "On a number line, start at 3 and move 4 steps right to land on 7.",
            &["3 + 4 = 7", "4 steps right from 3 lands on 7"],
        ),
];

const SUBTRACT_BEATS: &[Beat] = &[
    Beat::new("start with 7 dots", BEAT_MS)
        .note(
            "Seven dots sit in one tray. The last four are red because they are the ones that will be taken away.",
            "a row of seven dots on the tray, the right four red",
        )
        .detail(
            "Subtraction starts from an amount you have, then removes part of it.",
            &["7 dots at the start", "7 - 4 = 3 is what is left"],
        ),
    Beat::new("take away 4", BEAT_MS)
        .note(
            "The four red dots slide off the tray to the side. The count that stays on the tray is what subtraction measures.",
            "four red dots moving to the tray on the right while three dots stay on the left",
        )
        .detail(
            "Taking away is the same as counting what is left after the removal.",
            &["4 dots taken away", "7 - 4 = 3"],
        ),
    Beat::new("what is left: 3", BEAT_MS)
        .note(
            "Three dots remain on the tray. That is the answer.",
            "three dots on the left tray, tagged 7 - 4 = 3",
        )
        .detail(
            "Check it with addition: subtraction undoes addition.",
            &["7 - 4 = 3", "Check: 3 + 4 = 7"],
        ),
];

const MULTIPLY_BEATS: &[Beat] = &[
    Beat::new("3 groups of 4 dots", BEAT_MS)
        .note(
            "Three separate groups stand side by side, each with 4 dots.",
            "three groups of four dots on their own floors, tagged group 1, 2 and 3",
        )
        .detail(
            "Multiplying is adding equal groups: 3 x 4 means 3 groups of 4.",
            &["4 + 4 + 4 = 12", "3 groups of 4 dots"],
        ),
    Beat::new("stack the groups into rows", BEAT_MS)
        .note(
            "Each group slides into its own row of one grid: 3 rows of 4 dots, the same 12 dots.",
            "three coloured rows of four dots rising into a grid",
        )
        .detail(
            "The same dots arranged as a rectangle show multiplication as counting a grid.",
            &["3 rows x 4 per row = 12", "A 4 by 3 rectangle holds 12 unit squares"],
        ),
    Beat::new("3 x 4 = 12", BEAT_MS)
        .note(
            "All 12 dots form the grid: 3 rows of 4. It is the same count as 4 + 4 + 4.",
            "the finished grid of 12 dots, tagged 3 x 4 = 12",
        )
        .detail(
            "Swapping the two numbers never changes the product.",
            &["3 x 4 = 12", "4 x 3 = 12 too"],
        ),
];

const DIVIDE_BEATS: &[Beat] = &[
    Beat::new("12 dots to share", BEAT_MS)
        .note(
            "Twelve dots in a grid of 3 rows and 4 dots, ready to be shared out.",
            "the 12-dot grid with its tag",
        )
        .detail(
            "Division asks how many dots go in each share.",
            &["12 dots", "12 / 4 is the size of each share"],
        ),
    Beat::new("deal one dot at a time", BEAT_MS)
        .note(
            "Dots are dealt one at a time into four groups, round after round, so every group gets the same.",
            "dots travelling from the grid into four groups, each group taking one dot per round",
        )
        .detail(
            "Dealing equally is sharing: each group ends with the same count.",
            &["4 groups", "3 rounds of 4 dots = 12 dots"],
        ),
    Beat::new("12 / 4 = 3 in each group", BEAT_MS)
        .note(
            "Each of the four groups has 3 dots and none are left over.",
            "four groups of three dots, tagged group 1 to group 4",
        )
        .detail(
            "Division undoes multiplication: 4 x 3 = 12, so 12 / 4 = 3.",
            &["12 / 4 = 3", "4 x 3 = 12 checks it"],
        ),
];

const VECTOR_BEATS: &[Beat] = &[
    Beat::new("a vector: an ordered list of numbers", BEAT_MS)
        .note(
            "The list v = [2, 5, 1] drawn as three bars, one per slot. Slot 1 is 2, slot 2 is 5, slot 3 is 1.",
            "three gold bars of heights 2, 5 and 1 standing on a floor",
        )
        .detail(
            "A vector is an ordered list: each slot holds one number, and the order matters.",
            &["v = [2, 5, 1]", "3 slots: slot 1 = 2, slot 2 = 5, slot 3 = 1"],
        ),
    Beat::new("the same list as an arrow", BEAT_MS)
        .note(
            "The three numbers become an arrow from the origin: 2 steps along x, 5 up y, 1 toward you.",
            "the cyan arrow from the origin with the x, y and z axes drawn through it",
        )
        .detail(
            "A vector is also a point or an arrow in space, which is how a model stores positions and directions.",
            &["tip at (2, 5, 1)", "axes: x across, y up, z toward you"],
        ),
    Beat::new("steps to the tip", BEAT_MS)
        .note(
            "The arrow's path is three steps: 2 along x, then 5 up, then 1 toward you, ending at the tip.",
            "the grey staircase of three segments running along the arrow to its tip",
        )
        .detail(
            "Each slot is one step along one axis.",
            &["2 + 5 + 1 steps", "tip at (2, 5, 1)"],
        ),
];

const VECTOR_ADD_BEATS: &[Beat] = &[
    Beat::new("a = [1, 2]: an arrow from the origin", BEAT_MS)
        .note(
            "Arrow a runs from the origin to the point 1 step right and 2 steps up.",
            "the gold arrow with its tip at 1 right and 2 up",
        )
        .detail(
            "A pair of numbers is a point, or an arrow from the origin to that point.",
            &["a = [1, 2]"],
        ),
    Beat::new("move b to the tip of a", BEAT_MS)
        .note(
            "Arrow b = [3, 4] slides so its tail sits on the tip of a. Its length and direction do not change.",
            "the blue arrow sliding from the origin until its tail meets the tip of the gold arrow",
        )
        .detail(
            "Tip to tail: the sum starts at the first tail and ends at the last tip.",
            &["b = [3, 4]", "b's tail moved by a = [1, 2]"],
        ),
    Beat::new("a + b = [4, 6]", BEAT_MS)
        .note(
            "The sum is the green arrow from the origin to where b now ends.",
            "the green arrow from the origin to the tip of b after the move",
        )
        .detail(
            "Adding vectors adds slot by slot.",
            &["[1, 2] + [3, 4] = [4, 6]", "1 + 3 = 4 and 2 + 4 = 6"],
        ),
];

const SCALE_BEATS: &[Beat] = &[
    Beat::new("the arrow [1, 2] before scaling", BEAT_MS)
        .note(
            "The arrow from the origin to [1, 2], at its normal length.",
            "a single gold arrow from the origin",
        )
        .detail(
            "Scaling multiplies every slot by the same number.",
            &["[1, 2]", "slot 1 = 1, slot 2 = 2"],
        ),
    Beat::new("grow every slot by 3", BEAT_MS)
        .note(
            "The arrow stretches to three times its length. The faint outline is the original.",
            "the gold arrow growing past the faint outline of the original",
        )
        .detail(
            "Scaling by 3 keeps the direction and multiplies the length by 3.",
            &["3 x 1 = 3", "3 x 2 = 6"],
        ),
    Beat::new("3 x [1, 2] = [3, 6]", BEAT_MS)
        .note(
            "The stretched arrow ends at (3, 6). A scale of -1 would flip it to point the other way.",
            "the long gold arrow with the tag 3 x [1, 2] = [3, 6]",
        )
        .detail(
            "Multiplying every slot by one number is a scale, the basic step before adding vectors together.",
            &["3 x [1, 2] = [3, 6]", "2 x an arrow doubles it; -1 x flips it"],
        ),
];

const DOT_PRODUCT_BEATS: &[Beat] = &[
    Beat::new("a = [1, 2, 3] and b = [4, 5, 6]", BEAT_MS)
        .note(
            "Two lists drawn as bars, slot by slot: blue for a, gold for b.",
            "blue bars for a (1, 2, 3) and gold bars for b (4, 5, 6) on one floor",
        )
        .detail(
            "The dot product takes two vectors of the same length and returns one number.",
            &["a = [1, 2, 3]", "b = [4, 5, 6]", "3 slots each"],
        ),
    Beat::new("multiply each pair of slots", BEAT_MS)
        .note(
            "Each pair of slots is multiplied, giving three products: 1 x 4, 2 x 5 and 3 x 6.",
            "the green product bars rising to 4, 10 and 18",
        )
        .detail(
            "Each slot pair gives one product; the products are added next.",
            &["1 x 4 = 4", "2 x 5 = 10", "3 x 6 = 18"],
        ),
    Beat::new("add the products: 32", BEAT_MS)
        .note(
            "The three product bars stack into one column whose height is their sum.",
            "the green stack with the tag 4 + 10 + 18 = 32",
        )
        .detail(
            "A neuron computes this sum with its weights: the dot product of its inputs and weights.",
            &["4 + 10 + 18 = 32", "a . b = 32"],
        ),
];

const MATRIX_BEATS: &[Beat] = &[
    Beat::new("a 2 x 3 matrix: a grid of numbers", BEAT_MS)
        .note(
            "A grid with 2 rows and 3 columns: six numbers, shape (2 x 3).",
            "a grid of six tiles, two rows of three",
        )
        .detail(
            "A matrix is a grid; its shape is rows by columns.",
            &["2 rows x 3 columns", "6 numbers"],
        ),
    Beat::new("row 1 runs across", BEAT_MS)
        .note(
            "Row 1 lights up across all three columns.",
            "the top row lit gold, tagged row 1 = [1, 2, 3]",
        )
        .detail(
            "A row is read across the grid.",
            &["row 1 = [1, 2, 3]", "A[1][3] = 3"],
        ),
    Beat::new("column 2 runs down", BEAT_MS)
        .note(
            "Column 2 lights up down both rows.",
            "the middle column lit gold, tagged column 2 = [2, 5]",
        )
        .detail(
            "A column is read down the grid.",
            &["column 2 = [2, 5]", "A[2][2] = 5"],
        ),
];

const SHAPE_RULE_BEATS: &[Beat] = &[
    Beat::new("A is 2 x 3, B is 3 x 2", BEAT_MS)
        .note(
            "Two matrices side by side: A with 2 rows and 3 columns, B with 3 rows and 2 columns.",
            "A's grid on the left and B's grid in the middle",
        )
        .detail(
            "Multiplication needs the shapes to fit together.",
            &["A: (2 x 3)", "B: (3 x 2)"],
        ),
    Beat::new("the inner 3 and 3 match", BEAT_MS)
        .note(
            "A's three columns and B's three rows line up, so the product exists.",
            "a gold bracket over A's three columns and a cyan bracket beside B's three rows",
        )
        .detail(
            "The inner sizes are used up by the dot products; the outer sizes give the answer's shape.",
            &["(m x n)(n x p) = (m x p)", "inner: 3 = 3"],
        ),
    Beat::new("the answer is 2 x 2", BEAT_MS)
        .note(
            "The product takes the outer sizes: 2 rows and 2 columns, the green grid on the right.",
            "the green 2 x 2 grid on the right",
        )
        .detail(
            "Order matters: A x B is 2 x 2, but B x A is 3 x 3.",
            &["(2 x 3)(3 x 2) = (2 x 2)", "(3 x 2)(2 x 3) = (3 x 3)"],
        ),
];

const MATRIX_VECTOR_BEATS: &[Beat] = &[
    Beat::new("A (2 x 2) times v (2 x 1)", BEAT_MS)
        .note(
            "A matrix, a column vector, and an empty answer column. The answer is a (2 x 1) vector.",
            "A's 2 x 2 grid, v's column, and the empty answer column on the right",
        )
        .detail(
            "Each answer slot is one row of A dotted with v.",
            &["A = [[1, 2], [3, 4]]", "v = [5, 6]"],
        ),
    Beat::new("slot 1: row 1 . v = 17", BEAT_MS)
        .note(
            "Row 1 of A and v are multiplied slot by slot and added into answer slot 1.",
            "row 1 and v lit, answer slot 1 lit green with 17",
        )
        .detail(
            "A layer computes W v: each row of W gives one output.",
            &["1 x 5 + 2 x 6 = 17", "answer slot 1 = 17"],
        ),
    Beat::new("slot 2: row 2 . v = 39", BEAT_MS)
        .note(
            "Row 2 of A dotted with v gives answer slot 2.",
            "row 2 lit, answer slot 2 lit green with 39",
        )
        .detail(
            "Stacking more rows gives more outputs at once.",
            &["3 x 5 + 4 x 6 = 39", "A v = [17, 39]"],
        ),
];

const MATRIX_MATRIX_BEATS: &[Beat] = &[
    Beat::new("A (2 x 2) and B (2 x 2)", BEAT_MS)
        .note(
            "Two 2 by 2 matrices, A on the left and B in the middle, and an empty answer C on the right.",
            "three grids: A left, B middle, C right, C still empty",
        )
        .detail(
            "The answer C is filled one cell at a time.",
            &["A = [[1, 2], [3, 4]]", "B = [[5, 6], [7, 8]]"],
        ),
    Beat::new("cell 1,1 = row 1 . column 1 = 19", BEAT_MS)
        .note(
            "Row 1 of A and column 1 of B are dotted to fill the top-left cell of C.",
            "row 1 of A and column 1 of B lit, C's top-left cell lit with 19",
        )
        .detail(
            "Each answer cell is one dot product: row i of A with column j of B.",
            &["1 x 5 + 2 x 7 = 19", "C[1][1] = 19"],
        ),
    Beat::new("all four cells: C = [[19, 22], [43, 50]]", BEAT_MS)
        .note(
            "The other three cells follow the same rule, which gives the whole product.",
            "all four cells of C lit, tagged 19, 22, 43 and 50",
        )
        .detail(
            "Large models are mostly matrix products, and GPUs compute many of these dot products at once.",
            &["C = [[19, 22], [43, 50]]", "2 x 2 x 2 = 8 multiplies"],
        ),
];

math_page!(add, ADD_CELL, ADD_BEATS, "add");
math_page!(subtract, SUBTRACT_CELL, SUBTRACT_BEATS, "subtract");
math_page!(multiply, MULTIPLY_CELL, MULTIPLY_BEATS, "multiply");
math_page!(divide, DIVIDE_CELL, DIVIDE_BEATS, "divide");
math_page!(vector, VECTOR_CELL, VECTOR_BEATS, "vector");
math_page!(vector_add, VECTOR_ADD_CELL, VECTOR_ADD_BEATS, "vector_add");
math_page!(scale, SCALE_CELL, SCALE_BEATS, "scale");
math_page!(dot_product, DOT_PRODUCT_CELL, DOT_PRODUCT_BEATS, "dot_product");
math_page!(matrix, MATRIX_CELL, MATRIX_BEATS, "matrix");
math_page!(shape_rule, SHAPE_RULE_CELL, SHAPE_RULE_BEATS, "shape_rule");
math_page!(matrix_vector, MATRIX_VECTOR_CELL, MATRIX_VECTOR_BEATS, "matrix_vector");
math_page!(matrix_matrix, MATRIX_MATRIX_CELL, MATRIX_MATRIX_BEATS, "matrix_matrix");

pub const NODES: &[Node] = &[
    Node { page: "ADD", overview: Some(add), sections: &[], clips: false },
    Node { page: "SUBTRACT", overview: Some(subtract), sections: &[], clips: false },
    Node { page: "MULTIPLY", overview: Some(multiply), sections: &[], clips: false },
    Node { page: "DIVIDE", overview: Some(divide), sections: &[], clips: false },
    Node { page: "VECTOR", overview: Some(vector), sections: &[], clips: false },
    Node { page: "VECTOR ADD", overview: Some(vector_add), sections: &[], clips: false },
    Node { page: "SCALE", overview: Some(scale), sections: &[], clips: false },
    Node { page: "DOT PRODUCT", overview: Some(dot_product), sections: &[], clips: false },
    Node { page: "MATRIX", overview: Some(matrix), sections: &[], clips: false },
    Node { page: "SHAPE RULE", overview: Some(shape_rule), sections: &[], clips: false },
    Node { page: "MATRIX x VECTOR", overview: Some(matrix_vector), sections: &[], clips: false },
    Node { page: "MATRIX x MATRIX", overview: Some(matrix_matrix), sections: &[], clips: false },
];

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn every_math_overview_is_explained_and_draws_every_beat() {
        assert_eq!(NODES.len(), 12);
        for n in NODES {
            let build = n.overview.expect("every math page has an overview");
            let s = build();
            assert_eq!(s.beats().len(), 3, "{}: three beats", n.page);
            blender::explained(s.as_ref(), n.page);
            blender::draws_every_beat(s.as_ref(), n.page);
        }
    }
}
