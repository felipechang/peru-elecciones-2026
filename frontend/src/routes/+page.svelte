<script lang="ts">
	import type { PageData } from './$types';

	let { data }: { data: PageData } = $props();

	const features = [
		{ icon: '🏛️', title: 'Partidos', desc: 'Conoce los partidos, sus estatutos e idearios.', href: '/partidos' },
		{ icon: '🙋', title: 'Candidatos', desc: 'Busca candidatos por nombre, cargo o partido.', href: '/candidatos' },
		{ icon: '📋', title: 'Comparar Temas', desc: 'Compara las propuestas de todos los partidos por tema.', href: '/temas' },
		{ icon: '📰', title: 'Noticias', desc: 'Últimas noticias sobre los candidatos.', href: '/noticias' }
	];
</script>

<!-- Hero -->
<section class="text-center py-12">
	<div class="inline-flex items-center gap-3 mb-4">
		<span class="text-5xl">🇵🇪</span>
	</div>
	<h1 class="text-4xl font-black text-gray-900 mb-3">Peru Elecciones 2026</h1>
	<p class="text-xl text-gray-600 max-w-2xl mx-auto">
		Información clara e imparcial sobre partidos, candidatos y propuestas para que puedas votar con conocimiento.
	</p>
</section>

<!-- Feature cards -->
<section class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-12">
	{#each features as f}
		<a
			href={f.href}
			class="bg-white rounded-xl border border-gray-200 p-6 hover:border-red-400 hover:shadow-md transition-all group"
		>
			<div class="text-3xl mb-3">{f.icon}</div>
			<h2 class="font-bold text-lg mb-1 group-hover:text-red-700">{f.title}</h2>
			<p class="text-sm text-gray-500">{f.desc}</p>
		</a>
	{/each}
</section>

<!-- Latest news -->
<section>
	<h2 class="text-xl font-bold mb-4 flex items-center gap-2">
		<span>📰</span> Últimas noticias
	</h2>

	{#if data.events.length === 0}
		<p class="text-gray-500 italic">Aún no hay noticias disponibles.</p>
	{:else}
		<div class="space-y-3">
			{#each data.events as ev}
				<div class="bg-white rounded-lg border border-gray-200 p-4 flex gap-4">
					<div class="shrink-0 text-xs text-gray-400 w-20 pt-0.5">
						{ev.event_date ?? '—'}
					</div>
					<div class="flex-1 min-w-0">
						<p class="font-medium text-sm leading-snug">{ev.title}</p>
						{#if ev.summary}
							<p class="text-xs text-gray-500 mt-1 line-clamp-2">{ev.summary}</p>
						{/if}
						<div class="flex gap-3 mt-1.5 text-xs text-gray-400">
							<a href="/candidatos/{ev.candidate_id}" class="hover:text-red-600 font-medium">{ev.candidate_name}</a>
							<span>·</span>
							<span>{ev.party_name}</span>
							{#if ev.source}
								<span>·</span>
								<a href={ev.source} target="_blank" rel="noopener" class="hover:text-red-600 truncate max-w-[160px]">fuente</a>
							{/if}
						</div>
					</div>
				</div>
			{/each}
		</div>
		<div class="mt-4 text-center">
			<a href="/noticias" class="text-sm text-red-700 hover:underline font-medium">Ver todas las noticias →</a>
		</div>
	{/if}
</section>
