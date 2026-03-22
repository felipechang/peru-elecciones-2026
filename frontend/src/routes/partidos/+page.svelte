<script lang="ts">
	import type { PageData } from './$types';

	let { data }: { data: PageData } = $props();

	let search = $state('');

	const filtered = $derived(
		search.trim()
			? data.parties.filter((p) => p.name.toLowerCase().includes(search.toLowerCase()))
			: data.parties
	);
</script>

<svelte:head><title>Partidos — Peru Elecciones 2026</title></svelte:head>

<h1 class="text-3xl font-black mb-2">Partidos Políticos</h1>
<p class="text-gray-500 mb-6">Todos los partidos que participan en las elecciones generales 2026.</p>

<input
	type="search"
	bind:value={search}
	placeholder="Buscar partido..."
	class="w-full max-w-md border border-gray-300 rounded-lg px-4 py-2 mb-6 focus:outline-none focus:ring-2 focus:ring-red-400"
/>

{#if filtered.length === 0}
	<p class="text-gray-500 italic">No se encontraron partidos.</p>
{:else}
	<div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
		{#each filtered as party}
			<a
				href="/partidos/{party.id}"
				class="bg-white rounded-xl border border-gray-200 p-5 hover:border-red-400 hover:shadow-md transition-all group"
			>
				<h2 class="font-bold text-base mb-2 group-hover:text-red-700 leading-snug">{party.name}</h2>
				{#if party.summary}
					<p class="text-sm text-gray-500 line-clamp-3">{party.summary}</p>
				{:else}
					<p class="text-sm text-gray-400 italic">Sin resumen disponible.</p>
				{/if}
			</a>
		{/each}
	</div>
{/if}
