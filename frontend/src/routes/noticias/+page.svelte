<script lang="ts">
	import type { PageData } from './$types';
	import type { Event } from '$lib/server/db';

	let { data }: { data: PageData } = $props();

	const grouped = $derived(
		data.events.reduce<Record<string, Event[]>>((acc, ev) => {
			const date = ev.event_date ?? 'Sin fecha';
			(acc[date] ??= []).push(ev);
			return acc;
		}, {})
	);

	const sortedDates = $derived(
		Object.keys(grouped).sort((a, b) => {
			if (a === 'Sin fecha') return 1;
			if (b === 'Sin fecha') return -1;
			return b.localeCompare(a);
		})
	);
</script>

<svelte:head><title>Noticias — Peru Elecciones 2026</title></svelte:head>

<h1 class="text-3xl font-black mb-2">Noticias</h1>
<p class="text-gray-500 mb-6">Últimas noticias sobre candidatos, actualizadas automáticamente.</p>

{#if data.events.length === 0}
	<p class="text-gray-500 italic">No hay noticias disponibles aún.</p>
{:else}
	<div class="space-y-8">
		{#each sortedDates as date}
			<section>
				<h2 class="text-sm font-bold text-gray-500 uppercase tracking-wider mb-3 flex items-center gap-2">
					<span class="h-px flex-1 bg-gray-200"></span>
					{date}
					<span class="h-px flex-1 bg-gray-200"></span>
				</h2>
				<div class="space-y-3">
					{#each grouped[date] as ev}
						<div class="bg-white border border-gray-200 rounded-xl p-4 hover:border-red-300 transition-colors">
							<div class="flex items-start justify-between gap-4">
								<div class="flex-1 min-w-0">
									<h3 class="font-semibold text-sm leading-snug mb-1">{ev.title}</h3>
									{#if ev.summary}
										<p class="text-sm text-gray-600 leading-relaxed line-clamp-3">{ev.summary}</p>
									{/if}
									<div class="flex flex-wrap gap-3 mt-2 text-xs text-gray-400">
										<a href="/candidatos/{ev.candidate_id}" class="hover:text-red-600 font-medium">
											{ev.candidate_name}
										</a>
										<span>·</span>
										<span>{ev.party_name}</span>
										{#if ev.source}
											<span>·</span>
											<a href={ev.source} target="_blank" rel="noopener" class="hover:text-red-600">
												Ver fuente →
											</a>
										{/if}
									</div>
								</div>
							</div>
						</div>
					{/each}
				</div>
			</section>
		{/each}
	</div>

	{#if data.events.length >= data.limit}
		<div class="text-center mt-8">
			<a
				href="/noticias?limit={data.limit + 50}"
				class="bg-white border border-gray-300 text-gray-700 px-6 py-2 rounded-lg text-sm hover:bg-gray-50 transition-colors inline-block"
			>
				Cargar más noticias
			</a>
		</div>
	{/if}
{/if}
