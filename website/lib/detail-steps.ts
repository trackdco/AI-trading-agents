export type StepId = "foam" | "wash" | "clay" | "iron" | "coat";

export type DetailStep = {
  id: StepId;
  label: string;
  /** One line under the video. Keep it short; it sits on a single line on desktop. */
  short: string;
  /** Drop an mp4 in public/media/steps and put its path here to light the step up. */
  video: string | null;
  poster: string;
  /** What the footage shows, for anyone who can't see it. */
  alt: string;
};

const PLACEHOLDER = "/media/steps/placeholder.webp";

// The five stages of an exterior detail, in the order they happen. This array is
// the whole config: adding footage for a step is one line, the `video` path.
export const detailSteps: DetailStep[] = [
  {
    id: "foam",
    label: "Snow foam",
    short: "A thick layer of foam sits on the paint and lifts the loose grit off before anything touches it.",
    video: "/media/steps/snow-foam.mp4",
    poster: "/media/steps/snow-foam.webp",
    alt: "Thick white snow foam being laid over a car and sliding down the panels",
  },
  {
    id: "wash",
    label: "Touch wash",
    short: "Two buckets, a clean mitt and pH-neutral shampoo, one panel at a time, rinsing after every pass.",
    video: null,
    poster: PLACEHOLDER,
    alt: "A two-bucket contact wash",
  },
  {
    id: "clay",
    label: "Clay bar",
    short: "Clay glides over lubricated paint and pulls out what's bonded into it: overspray, rail dust and sap.",
    video: null,
    poster: PLACEHOLDER,
    alt: "A clay bar being worked across lubricated paint",
  },
  {
    id: "iron",
    label: "Iron decon",
    short: "A chemical that reacts with the iron thrown off your brakes and turns deep purple as it dissolves it.",
    video: null,
    poster: PLACEHOLDER,
    alt: "Iron remover bleeding purple down a panel",
  },
  {
    id: "coat",
    label: "Ceramic sealant",
    short: "The protection goes on last, panel by panel, and cures hard onto the clear coat.",
    video: null,
    poster: PLACEHOLDER,
    alt: "Ceramic sealant being spread across a panel",
  },
];
