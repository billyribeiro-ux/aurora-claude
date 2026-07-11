import adapter from '@sveltejs/adapter-node';
import { sveltekit } from '@sveltejs/kit/vite';
import { defineConfig } from 'vite';

export default defineConfig({
	plugins: [
		sveltekit({
			compilerOptions: {
				// Force runes mode for the project, except for libraries. Can be removed in svelte 6.
				runes: ({ filename }) =>
					filename.split(/[/\\]/).includes('node_modules') ? undefined : true
			},

			// adapter-node builds a standalone Node server (`node build`). It reads
			// runtime environment variables (e.g. FMP_API_KEY) via process.env, which
			// is exactly what `$env/dynamic/private` needs.
			adapter: adapter()
		})
	]
});
