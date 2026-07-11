<script lang="ts">
	interface Props {
		data: number[];
		width?: number;
		height?: number;
		strokeWidth?: number;
	}

	let { data, width = 120, height = 32, strokeWidth = 1.5 }: Props = $props();

	const up = $derived(data.length >= 2 ? data[data.length - 1] >= data[0] : true);

	const line = $derived.by(() => {
		if (data.length < 2) return '';
		const min = Math.min(...data);
		const max = Math.max(...data);
		const span = max - min || 1;
		const stepX = width / (data.length - 1);
		return data
			.map((v, i) => {
				const x = (i * stepX).toFixed(2);
				const y = (height - ((v - min) / span) * height).toFixed(2);
				return `${i === 0 ? 'M' : 'L'}${x},${y}`;
			})
			.join(' ');
	});

	const area = $derived(line ? `${line} L${width},${height} L0,${height} Z` : '');
	const color = $derived(up ? 'var(--up)' : 'var(--down)');
</script>

<svg
	class="spark"
	viewBox="0 0 {width} {height}"
	{width}
	{height}
	preserveAspectRatio="none"
	aria-hidden="true"
>
	{#if area}
		<path d={area} fill={color} fill-opacity="0.12" stroke="none" />
	{/if}
	<path
		d={line}
		fill="none"
		stroke={color}
		stroke-width={strokeWidth}
		stroke-linecap="round"
		stroke-linejoin="round"
		vector-effect="non-scaling-stroke"
	/>
</svg>

<style>
	.spark {
		display: block;
		overflow: visible;
	}
</style>
