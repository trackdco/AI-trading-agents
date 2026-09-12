import { LoopVideo } from "@/components/site/loop-video";

// The hydrophobic beading loop used in the gallery.
export function BeadingVideo({ className = "" }: { className?: string }) {
  return <LoopVideo base="/media/beading-720" poster="/media/beading-poster.jpg" label="Water beading and sliding off a ceramic-coated panel" className={className} />;
}
