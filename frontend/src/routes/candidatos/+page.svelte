<script lang="ts">
	import type { PageData } from './$types';

	let { data }: { data: PageData } = $props();

	const POSITIONS = ['', 'Presidente', 'Vicepresidente', 'Senador', 'Congresista', 'Parlamento Andino'];

	const totalPages = $derived(Math.ceil(data.total / data.pageSize));

	function pageUrl(p: number) {
		const params = new URLSearchParams();
		if (data.q) params.set('q', data.q);
		if (data.position) params.set('position', data.position);
		if (data.partyId) params.set('party_id', String(data.partyId));
		if (p > 1) params.set('page', String(p));
		const qs = params.toString();
		return `/candidatos${qs ? '?' + qs : ''}`;
	}
</script>

<svelte:head><title>Candidatos — Peru Elecciones 2026</title></svelte:head>

<h1 class="text-3xl font-black mb-2">Candidatos</h1>
<p class="text-gray-500 mb-6">Busca candidatos por nombre, cargo o partido.</p>

<form method="GET" class="flex flex-wrap gap-3 mb-6">
	<input
		type="search"
		name="q"
		value={data.q}
		placeholder="Nombre del candidato..."
		class="flex-1 min-w-48 border border-gray-300 rounded-lg px-4 py-2 focus:outline-none focus:ring-2 focus:ring-red-400"
	/>
	<select
		name="position"
		class="border border-gray-300 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-red-400"
	>
		{#each POSITIONS as pos}
			<option value={pos} selected={data.position === pos}>{pos || 'Todos los cargos'}</option>
		{/each}
	</select>
	<select
		name="party_id"
		class="border border-gray-300 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-red-400 max-w-56"
	>
		<option value="0" selected={!data.partyId}>Todos los partidos</option>
		{#each data.parties as p}
			<option value={p.id} selected={data.partyId === p.id}>{p.name}</option>
		{/each}
	</select>
	<button
		type="submit"
		class="bg-red-700 text-white px-5 py-2 rounded-lg font-medium hover:bg-red-800 transition-colors"
	>
		Buscar
	</button>
</form>

<p class="text-sm text-gray-500 mb-4">{data.total.toLocaleString()} candidatos encontrados</p>

{#if data.candidates.length === 0}
	<p class="text-gray-500 italic">No se encontraron candidatos.</p>
{:else}
	<div class="bg-white rounded-xl border border-gray-200 overflow-hidden">
		<table class="w-full text-sm">
			<thead class="bg-gray-50 border-b border-gray-200">
				<tr>
					<th class="text-left px-4 py-3 font-semibold text-gray-600">Nombre</th>
					<th class="text-left px-4 py-3 font-semibold text-gray-600 hidden sm:table-cell">Cargo</th>
					<th class="text-left px-4 py-3 font-semibold text-gray-600 hidden md:table-cell">Partido</th>
					<th class="text-left px-4 py-3 font-semibold text-gray-600 hidden lg:table-cell">Ámbito</th>
				</tr>
			</thead>
			<tbody class="divide-y divide-gray-100">
				{#each data.candidates as c}
					<tr class="hover:bg-gray-50 transition-colors">
						<td class="px-4 py-3">
							<a href="/candidatos/{c.id}" class="font-medium hover:text-red-700">{c.name}</a>
							<div class="sm:hidden text-xs text-gray-400 mt-0.5">{c.position} · {c.party_name}</div>
						</td>
						<td class="px-4 py-3 text-gray-600 hidden sm:table-cell">{c.position}</td>
						<td class="px-4 py-3 hidden md:table-cell">
							<a href="/partidos/{c.party_id}" class="text-red-700 hover:underline">{c.party_name}</a>
						</td>
						<td class="px-4 py-3 text-gray-500 hidden lg:table-cell">{c.scope ?? '—'}</td>
					</tr>
				{/each}
			</tbody>
		</table>
	</div>

	<!-- Pagination -->
	{#if totalPages > 1}
		<div class="flex justify-center gap-1 mt-6">
			<a
				href={pageUrl(data.page - 1)}
				aria-disabled={data.page === 1}
				class="px-3 py-1.5 rounded border text-sm {data.page === 1 ? 'opacity-40 pointer-events-none' : 'hover:bg-gray-100'}"
			>←</a>
			{#each Array(Math.min(totalPages, 7)) as _, i}
				{@const p = i + 1}
				<a
					href={pageUrl(p)}
					class="px-3 py-1.5 rounded border text-sm transition-colors
						{p === data.page ? 'bg-red-700 text-white border-red-700' : 'hover:bg-gray-100'}"
				>{p}</a>
			{/each}
			{#if totalPages > 7}
				<span class="px-2 py-1.5 text-gray-400 text-sm">…</span>
				<a href={pageUrl(totalPages)} class="px-3 py-1.5 rounded border text-sm hover:bg-gray-100">{totalPages}</a>
			{/if}
			<a
				href={pageUrl(data.page + 1)}
				aria-disabled={data.page === totalPages}
				class="px-3 py-1.5 rounded border text-sm {data.page === totalPages ? 'opacity-40 pointer-events-none' : 'hover:bg-gray-100'}"
			>→</a>
		</div>
	{/if}
{/if}
