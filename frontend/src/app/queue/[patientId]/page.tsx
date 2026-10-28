import { ArrowLeft } from "lucide-react";
import Link from "next/link";

import { CaseReviewClient } from "@/components/CaseReviewClient";
import { Callout } from "@/components/ui/Callout";
import { getCase } from "@/lib/api";

export const dynamic = "force-dynamic";

export default async function CaseDetailPage({
  params,
}: {
  params: Promise<{ patientId: string }>;
}) {
  const { patientId } = await params;

  let body;
  try {
    const initialCase = await getCase(patientId);
    body = <CaseReviewClient patientId={patientId} initialCase={initialCase} />;
  } catch (err) {
    const message = err instanceof Error ? err.message : String(err);
    body = (
      <Callout variant="warning" title="Could not load this case">
        {message}
      </Callout>
    );
  }

  return (
    <main>
      <Link
        href="/queue"
        className="mb-6 inline-flex items-center gap-1 text-sm font-medium text-slate-500 hover:text-teal-700 dark:text-slate-400 dark:hover:text-teal-400"
      >
        <ArrowLeft className="h-4 w-4" aria-hidden /> Back to the review queue
      </Link>
      {body}
    </main>
  );
}
