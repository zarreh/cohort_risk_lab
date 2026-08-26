import { getCase } from "@/lib/api";
import { CaseReviewClient } from "@/components/CaseReviewClient";

export const dynamic = "force-dynamic";

export default async function CaseDetailPage({
  params,
}: {
  params: Promise<{ patientId: string }>;
}) {
  const { patientId } = await params;

  try {
    const initialCase = await getCase(patientId);
    return (
      <main className="mx-auto max-w-3xl p-8 font-sans">
        <CaseReviewClient patientId={patientId} initialCase={initialCase} />
      </main>
    );
  } catch (err) {
    const message = err instanceof Error ? err.message : String(err);
    return (
      <main className="mx-auto max-w-3xl p-8 font-sans">
        <p className="rounded-lg border border-amber-300 bg-amber-50 p-4 text-sm text-amber-900 dark:border-amber-900 dark:bg-amber-950 dark:text-amber-200">
          Could not load this case ({message}).
        </p>
      </main>
    );
  }
}
