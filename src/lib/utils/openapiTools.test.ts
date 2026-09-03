import { describe, expect, it } from 'vitest';

import { convertOpenApiToToolPayload } from './index';

describe('OpenAPI tool schema stability', () => {
	it('sorts semantically unordered required fields', () => {
		const [tool] = convertOpenApiToToolPayload({
			paths: {
				'/input': {
					post: {
						operationId: 'send_process_input',
						requestBody: {
							content: {
								'application/json': {
									schema: {
										type: 'object',
										required: ['process_id', 'input'],
										properties: {
											process_id: { type: 'string' },
											input: { type: 'string' }
										}
									}
								}
							}
						}
					}
				}
			}
		});

		expect(tool.parameters.required).toEqual(['input', 'process_id']);
	});
});
