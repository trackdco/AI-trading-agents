export type StepId = "foam" | "wash" | "clay" | "iron" | "coat";

export type DetailStep = {
  id: StepId;
  label: string;
  title: string;
  what: string;
  why: string;
};

// The five stages of a proper exterior detail, in the order they happen.
export const detailSteps: DetailStep[] = [
  {
    id: "foam",
    label: "Snow foam",
    title: "Snow foam",
    what: "A thick layer of foam sits on the paint for a few minutes and lifts the loose grit off on its own.",
    why: "Most swirl marks get put there during the wash. Nothing touches the paint until the grit is already gone.",
  },
  {
    id: "wash",
    label: "Contact wash",
    title: "Contact wash",
    what: "Two buckets, a clean mitt and pH-neutral shampoo, one panel at a time, rinsing the mitt after every pass.",
    why: "A spinning brush drags the same grit across every panel. This is the slow way, and the only way that doesn't mark the paint.",
  },
  {
    id: "clay",
    label: "Clay bar",
    title: "Clay bar",
    what: "A clay bar glides over lubricated paint and pulls out what's bonded into it: overspray, rail dust and sap.",
    why: "Run a hand over the paint afterwards. It goes from sandpaper to glass. Nothing protects a surface that's still contaminated.",
  },
  {
    id: "iron",
    label: "Iron decon",
    title: "Iron decontamination",
    what: "A chemical that reacts with the iron particles thrown off your brakes and turns deep purple as it dissolves them.",
    why: "This is the one nobody believes until they watch it. Those particles rust inside your clear coat. The purple running off is the damage leaving.",
  },
  {
    id: "coat",
    label: "Ceramic sealant",
    title: "Ceramic sealant",
    what: "The protection goes on last, panel by panel, and cures hard onto the clear coat.",
    why: "Water beads and rolls off, dirt struggles to hold on, and every wash after this one takes half the time.",
  },
];
