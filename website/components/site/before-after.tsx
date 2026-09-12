import { CompareSlider } from "@/components/site/compare-slider";
import { SectionHeading } from "@/components/site/section-heading";

type Props = { before: string; after: string; caption: string; title?: string; intro?: string };

// The proof block: one real panel, swirls on one side, the corrected finish on the other.
export function BeforeAfter({ before, after, caption, title = "Before and after.", intro }: Props) {
  return (
    <section id="before-after" className="relative border-t border-border py-20 md:py-28">
      <div aria-hidden="true" className="pointer-events-none absolute inset-0 bg-[radial-gradient(45%_40%_at_80%_50%,rgba(31,111,196,0.14),transparent_70%)]" />
      <div className="container-x relative mx-auto grid max-w-6xl items-center gap-10 md:grid-cols-12">
        <div className="md:col-span-6">
          <SectionHeading title={title} intro={intro ?? caption} />
          <p className="max-w-[46ch] text-[15px] text-muted-foreground" data-reveal="up">
            Drag the handle. Same tailgate, same light. Two-step correction, then a ceramic coating.
          </p>
        </div>
        <div className="md:col-span-6 md:col-start-7" data-reveal="up">
          <CompareSlider
            before={before}
            after={after}
            beforeAlt="Tailgate before paint correction: swirl marks and wash scratches under the inspection light"
            afterAlt="The same tailgate after a two-step paint correction and ceramic coating: a clear, mirror-flat reflection"
          />
        </div>
      </div>
    </section>
  );
}
