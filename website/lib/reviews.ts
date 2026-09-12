import data from "./reviews.json";

export type Review = { name: string; time: string; quote: string };

// 45 real reviews, carried over from the current site's data.
export const reviews: Review[] = data as Review[];

export const featuredReviews = reviews.slice(0, 6);
