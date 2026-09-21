import Link from "next/link";

/**
 * The primary button above the fold on the service pages was an sms: link. On a
 * phone that opens the messages app with the job already written; on a Windows
 * or Linux laptop it does nothing at all — and a service page reached from a
 * Google search for "ceramic coating canberra" is very often opened on one.
 *
 * So the same button in the same place goes to the quote form on a desktop and
 * to the messages app on a phone. This is what the home page hero already does;
 * the pattern just was not shared. The display classes are written out rather
 * than passed to LinkButton, because its base class sets inline-flex and two
 * display utilities on one element resolve by stylesheet order, not by the
 * order they appear in the attribute.
 */
const base =
  "lift min-h-[52px] whitespace-nowrap items-center justify-center rounded-lg px-6 text-base font-semibold no-underline bg-accent text-accent-foreground hover:bg-[#5aa6f0]";

export function QuoteCta({ sms, formHref = "#book" }: { sms: string; formHref?: string }) {
  return (
    <>
      <Link href={formHref} className={`${base} hidden md:inline-flex`}>
        Get a quote
      </Link>
      <a href={sms} className={`${base} inline-flex md:hidden`}>
        Text us your car
      </a>
    </>
  );
}
