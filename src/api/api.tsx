export type ApiResult<T> = {
	ok: boolean;
	status: number;
	data: T | null;
};

type ApiClient = {
	get: <T = unknown>(path: string) => Promise<ApiResult<T>>;
};

const DEFAULT_BASE_URL = '';

async function requestJson<T>(url: string, init?: RequestInit): Promise<ApiResult<T>> {
	try {
		const response = await fetch(url, {
			...init,
			headers: {
				Accept: 'application/json',
				...(init?.headers ?? {}),
			},
		});

		const contentType = response.headers.get('content-type') ?? '';
		const isJson = contentType.includes('application/json');

		const data = (isJson ? await response.json() : await response.text()) as T;

		return {
			ok: response.ok,
			status: response.status,
			data: response.ok ? data : null,
		};
	} catch {
		return {
			ok: false,
			status: 0,
			data: null,
		};
	}
}

const api: ApiClient = {
	get: async <T = unknown>(path: string) => {
		const url = `${DEFAULT_BASE_URL}${path}`;
		return requestJson<T>(url, { method: 'GET' });
	},
};

export default api;