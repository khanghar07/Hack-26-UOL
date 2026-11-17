// Vercel and other proxies can return text or HTML when a function fails.
export async function readApiResponse(response) {
  const fallback = 'The CRM server could not complete this request (HTTP ' + response.status + '). Please retry.';
  let data;
  try {
    data = await response.json();
  } catch {
    throw new Error(fallback);
  }
  if (!response.ok) {
    const detail = data?.detail;
    const issues = detail?.issues?.map(issue => issue.path + ' — ' + issue.message);
    const fields = Array.isArray(detail) ? detail.map(issue => issue.msg) : [];
    throw new Error((typeof detail === 'string' && detail) || issues?.join('\n') || fields.join('\n') || detail?.message || fallback);
  }
  if (!data || typeof data !== 'object') throw new Error(fallback);
  return data;
}
