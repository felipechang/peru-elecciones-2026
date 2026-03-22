<script lang="ts">
	import '../app.css';
	import { page } from '$app/stores';

	let { children } = $props();

	const nav = [
		{ href: '/', label: 'Inicio' },
		{ href: '/partidos', label: 'Partidos' },
		{ href: '/candidatos', label: 'Candidatos' },
		{ href: '/temas', label: 'Comparar Temas' },
		{ href: '/noticias', label: 'Noticias' }
	];
</script>

<svelte:head>
	<title>Peru Elecciones 2026</title>
</svelte:head>

<div class="min-h-screen bg-gray-50 text-gray-900">
	<!-- Header -->
	<header class="bg-red-700 text-white shadow-md">
		<div class="mx-auto max-w-6xl px-4 py-3 flex items-center justify-between gap-4">
			<a href="/" class="flex items-center gap-2 font-bold text-lg tracking-tight shrink-0">
				<span class="text-2xl">🇵🇪</span>
				<span>Peru Elecciones <span class="font-black">2026</span></span>
			</a>
			<nav class="flex flex-wrap gap-1 text-sm">
				{#each nav as item}
					<a
						href={item.href}
						class="px-3 py-1.5 rounded-md font-medium transition-colors
							{$page.url.pathname === item.href
								? 'bg-white/20 text-white'
								: 'text-red-100 hover:bg-white/10 hover:text-white'}"
					>
						{item.label}
					</a>
				{/each}
			</nav>
		</div>
	</header>

	<!-- Main content -->
	<main class="mx-auto max-w-6xl px-4 py-8">
		{@render children()}
	</main>

	<!-- Footer -->
	<footer class="border-t border-gray-200 mt-16 py-6 text-center text-sm text-gray-500">
		Peru Elecciones 2026 — Plataforma de información cívica
	</footer>
</div>
