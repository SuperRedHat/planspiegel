/* eslint-disable @typescript-eslint/no-explicit-any */
import { IStep } from "@app/interfaces/check";
import { classNames } from "@app/utils/helpers";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import remarkRehype from "remark-rehype";
import { Chat } from "./Chat";

export default function CheckContent({
  item,
  chat_id,
  checkup_id,
  check_id,
}: {
  item: IStep;
  chat_id: string | undefined;
  checkup_id: string | undefined;
  check_id: string | undefined;
}) {
  return (
    <div className="w-full flex flex-col ">
      <div className="sm:flex sm:items-start sm:justify-between mb-4">
        <div>
          <h3 className="text-base font-semibold text-gray-900">{item.name}</h3>
        </div>
        <div className="mt-5 sm:ml-6 sm:mt-0 sm:flex sm:shrink-0 sm:items-center">
          {item.status === "upcoming" ? (
            <span className="inline-flex items-center rounded-full bg-gray-50 px-2 py-1 text-xs font-medium text-gray-700 ring-1 ring-inset ring-gray-600/20">
              Not started
            </span>
          ) : item.status === "current" ? (
            <span className="inline-flex items-center rounded-full bg-sky-50 px-2 py-1 text-xs font-medium text-sky-700 ring-1 ring-inset ring-sky-600/20">
              In progress
            </span>
          ) : item.status === "failed" ? (
            <span className="inline-flex items-center rounded-full bg-red-50 px-2 py-1 text-xs font-medium text-red-700 ring-1 ring-inset ring-red-600/20">
              Failed
            </span>
          ) : (
            <span className="inline-flex items-center rounded-full bg-green-50 px-2 py-1 text-xs font-medium text-green-700 ring-1 ring-inset ring-green-600/20">
              Done
            </span>
          )}
        </div>
      </div>
      {item.status === "complete" && item.tag === "cookie" && (
        <div className="border-t border-gray-200 py-4">
          <div className="space-y-4">
            <div>
              <h4 className="text-sm font-medium text-gray-600">
                GDPR Compliance Status
              </h4>
              <p
                className={`mt-1 text-sm ${
                  item.results?.gdpr_compliant
                    ? "text-green-600"
                    : "text-red-600"
                }`}
              >
                {item.results?.gdpr_compliant ? "Compliant" : "Non-compliant"}
              </p>
            </div>

            <div>
              <h4 className="text-sm font-medium text-gray-600">
                Cookie Categories
              </h4>
              <div className="mt-2 grid grid-cols-1 gap-2 sm:grid-cols-2">
                {item.results?.categories.map((category: any) => (
                  <div
                    key={category.identifier}
                    className="rounded-lg border border-gray-200 p-4"
                  >
                    <h5 className="font-medium text-gray-900">
                      {category.title}
                    </h5>
                    <p className="mt-1 text-sm text-gray-500">
                      {category.description}
                    </p>
                    <div className="mt-2">
                      <span
                        className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium ${
                          category.is_required
                            ? "bg-red-100 text-red-800"
                            : "bg-gray-100 text-gray-800"
                        }`}
                      >
                        {category.is_required ? "Required" : "Optional"}
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {item.results?.images && item.results.images.length > 0 && (
              <div>
                <h4 className="text-sm font-medium text-gray-600">
                  Screenshots
                </h4>
                <div className="mt-2 grid grid-cols-1 gap-4 sm:grid-cols-2">
                  {item.results.images.map((image: string, index: number) => (
                    <img
                      key={index}
                      src={image}
                      alt={`Screenshot ${index + 1}`}
                      className="rounded-lg border border-gray-200"
                    />
                  ))}
                </div>
              </div>
            )}
          </div>
          {item.results_description && (
            <dd className="mt-3 text-sm text-gray-600">
              {item.results_description}
            </dd>
          )}
        </div>
      )}
      {item.status === "complete" && item.tag === "lighthouse" && (
        <div className="border-t border-gray-200 py-4">
          <div className="space-y-4">
            {Object.entries(item.results?.audits || {})
              .filter(([key]) =>
                [
                  "is-on-https",
                  "redirects-http",
                  "deprecations",
                  "third-party-cookies",
                  "third-party-summary",
                  "csp-xss",
                  "has-hsts",
                  "origin-isolation",
                ].includes(key)
              )
              // @ts-expect-error cant avoid it
              // eslint-disable-next-line @typescript-eslint/no-unused-vars
              .map(([key, audit]: [string, any]) => (
                <div
                  key={audit.id}
                  className="rounded-lg border border-gray-200 p-4 break-inside-avoid"
                >
                  <div className="flex items-center justify-between">
                    <h5 className="font-medium text-gray-900">{audit.title}</h5>
                    {audit.score !== null && (
                      <span
                        className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium ${
                          audit.score === 1
                            ? "bg-green-100 text-green-800"
                            : audit.score === 0
                            ? "bg-red-100 text-red-800"
                            : "bg-yellow-100 text-yellow-800"
                        }`}
                      >
                        Score: {audit.score}
                      </span>
                    )}
                  </div>
                  <ReactMarkdown
                    remarkPlugins={[[remarkGfm], [remarkRehype]]}
                    className="prose prose-sm max-w-none mt-3"
                  >
                    {audit.description}
                  </ReactMarkdown>
                  {audit.displayValue && (
                    <p className="mt-2 text-sm font-medium text-gray-600">
                      {audit.displayValue}
                    </p>
                  )}
                  {audit.details?.items?.length > 0 && (
                    <div className="mt-4 overflow-x-auto">
                      <table className="min-w-full divide-y divide-gray-300">
                        <thead className="bg-gray-50">
                          <tr>
                            {audit.details.headings?.map(
                              (heading: any, index: number) => (
                                <th
                                  key={index}
                                  scope="col"
                                  className="px-3 py-3.5 text-left text-sm font-semibold text-gray-900"
                                >
                                  {heading.label}
                                </th>
                              )
                            )}
                          </tr>
                        </thead>
                        <tbody className="divide-y divide-gray-200 bg-white">
                          {audit.details.items?.map(
                            (item: any, index: number) => (
                              <tr key={index}>
                                {audit.details.headings?.map(
                                  (heading: any, colIndex: number) => (
                                    <td
                                      key={colIndex}
                                      className="whitespace-nowrap print:whitespace-normal px-3 py-4 text-sm text-gray-500"
                                    >
                                      {item[heading.key] &&
                                        JSON.stringify(item[heading.key])}
                                    </td>
                                  )
                                )}
                              </tr>
                            )
                          )}
                        </tbody>
                      </table>
                    </div>
                  )}
                </div>
              ))}
          </div>
        </div>
      )}
      {item.status === "complete" && item.tag === "technologies" && (
        <div className="border-t border-gray-200 py-4">
          {item.results?.retire_analysis[0] &&
          // @ts-expect-error known format
          Object.values(item.results?.retire_analysis[0])[0].length > 0 ? (
            <>
              <div className="text-sm font-medium text-gray-500 mb-4">
                Common Vulnerabilities and Exposures
              </div>
              <table className="min-w-full divide-y divide-gray-300 border-b border-gray-300">
                <thead className="bg-gray-100">
                  <tr>
                    <th
                      scope="col"
                      className="py-3.5 pl-4 pr-3 text-left text-sm font-semibold text-gray-900 sm:pl-6"
                    >
                      Component
                    </th>
                    <th
                      scope="col"
                      className="px-3 py-3.5 text-left text-sm font-semibold text-gray-900"
                    >
                      Version
                    </th>
                    <th
                      scope="col"
                      className="px-3 py-3.5 text-left text-sm font-semibold text-gray-900"
                    >
                      Severity
                    </th>
                    <th
                      scope="col"
                      className="px-3 py-3.5 text-left text-sm font-semibold text-gray-900"
                    >
                      Details
                    </th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-200 bg-white">
                  {item.results?.retire_analysis &&
                    item.results.retire_analysis.map((analysis: any) => {
                      const results = Object.values(analysis)[0];
                      // @ts-expect-error known format
                      return results
                        .map((result: any, i: number) => {
                          if (!result.vulnerabilities) return null;
                          return result.vulnerabilities.map(
                            (vuln: any, vulnIndex: number) => (
                              <tr key={`${i}-${result.component}-${vulnIndex}`}>
                                <td className="whitespace-nowrap print:whitespace-normal py-4 pl-4 pr-3 text-sm font-medium text-gray-900 sm:pl-6">
                                  {result.component}
                                </td>
                                <td className="whitespace-nowrap print:whitespace-normal px-3 py-4 text-sm text-gray-500">
                                  {result.version}
                                </td>
                                <td className="whitespace-nowrap print:whitespace-normal px-3 py-4 text-sm">
                                  <span
                                    className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium ${
                                      vuln.severity === "high"
                                        ? "bg-red-100 text-red-800"
                                        : vuln.severity === "medium"
                                        ? "bg-yellow-100 text-yellow-800"
                                        : "bg-blue-100 text-blue-800"
                                    }`}
                                  >
                                    {vuln.severity}
                                  </span>
                                </td>
                                <td className="px-3 py-4 text-sm text-gray-500">
                                  <div>{vuln.identifiers.summary}</div>
                                  {vuln.identifiers.CVE && (
                                    <div className="text-gray-600">
                                      CVE: {vuln.identifiers.CVE.join(", ")}
                                    </div>
                                  )}
                                </td>
                              </tr>
                            )
                          );
                        })
                        .filter(Boolean);
                    })}
                </tbody>
              </table>
            </>
          ) : (
            <div className="px-3 py-4 text-sm text-gray-500 text-center">
              No vulnerabilities found
            </div>
          )}
          {item.results_description && (
            <div className="text-sm text-gray-600 px-2 mt-4">
              {item.results_description}
            </div>
          )}
        </div>
      )}
      {item.status === "complete" && item.tag === "scan_ports" && (
        <div className="border-t border-gray-200 py-4">
          <dl className="grid grid-cols-1 gap-x-4 gap-y-4 sm:grid-cols-4">
            <div className="sm:col-span-4 px-2">
              <dt className="text-sm font-medium text-gray-500 mb-4">
                Open ports
              </dt>
              <dd className="mt-1 text-sm text-gray-900">
                {item.results?.open_ports?.map(
                  (port: number, index: number) => (
                    <span
                      key={index}
                      className={classNames(
                        "inline-flex items-center rounded-full px-2.5 py-0.5 text-sm font-medium mr-2 mb-2",
                        port === 80 || port === 443
                          ? "bg-green-100 text-green-800"
                          : "bg-red-100 text-red-800"
                      )}
                    >
                      {port}
                    </span>
                  )
                )}
              </dd>
              {item.results_description && (
                <dd className="mt-3 text-sm text-gray-600">
                  {item.results_description}
                </dd>
              )}
            </div>
          </dl>
        </div>
      )}
      {item.status === "complete" && item.tag === "network" && (
        <div className="border-t border-gray-200 py-4">
          <dl className="grid grid-cols-1 gap-x-4 gap-y-4 divide-y divide-gray-200 sm:grid-cols-4">
            {item.results?.results?.blacklist && (
              <div className="sm:col-span-4 px-2">
                <div className="flex flex-row space-x-8 mb-4">
                  <dt className="text-sm font-medium text-gray-900">
                    Blacklist
                  </dt>
                  <div className="flex gap-4">
                    <span className="inline-flex items-center rounded-full bg-green-100 px-2 text-xs font-medium text-green-800">
                      Passed:{" "}
                      {item.results?.results?.blacklist.data.Passed.length}
                    </span>
                    <span className="inline-flex items-center rounded-full bg-yellow-100 px-2 text-xs font-medium text-yellow-800">
                      Warnings:{" "}
                      {item.results?.results?.blacklist.data.Warnings.length}
                    </span>
                    <span className="inline-flex items-center rounded-full bg-red-100 px-2 text-xs font-medium text-red-800">
                      Failed:{" "}
                      {item.results?.results?.blacklist.data.Failed.length}
                    </span>
                  </div>
                </div>
                <span className="text-gray-500 text-sm">
                  Being listed on the blacklists can harm email deliverability
                  and reputation
                </span>
                <dd className="mt-1">
                  <div className="mt-6">
                    <h4 className="text-sm font-medium text-gray-900 mb-3">
                      Passed checks - the website is not blacklisted
                    </h4>
                    <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
                      {item.results?.results?.blacklist.data.Passed.map(
                        (check: any) => (
                          <div
                            key={check.ID}
                            className="border rounded-lg p-4 bg-green-50"
                          >
                            <div className="text-gray-900">{check.Name}</div>
                          </div>
                        )
                      )}
                    </div>
                  </div>
                  {item.results?.results?.blacklist.data.Warnings.length >
                    0 && (
                    <div className="mt-6">
                      <h4 className="text-sm font-medium text-gray-900 mb-3">
                        Blacklist warnings
                      </h4>
                      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
                        {item.results?.results?.blacklist.data.Warnings.map(
                          (check: any) => (
                            <div
                              key={check.ID}
                              className="border border-yellow-200 rounded-lg p-4 bg-yellow-50"
                            >
                              <div className="text-yellow-900">
                                {check.Name}
                              </div>
                              <div className="text-sm text-yellow-800 mt-1">
                                {check.Info}
                              </div>
                              {check.AdditionalInfo?.[0] && (
                                <div className="text-xs text-yellow-700 mt-1">
                                  {check.AdditionalInfo[0]}
                                </div>
                              )}
                            </div>
                          )
                        )}
                      </div>
                    </div>
                  )}

                  {item.results?.results?.blacklist.data.Failed.length > 0 && (
                    <div className="mt-6">
                      <h4 className="text-sm font-medium text-gray-900 mb-3">
                        Failed checks - the website is blacklisted
                      </h4>
                      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
                        {item.results?.results?.blacklist.data.Failed.map(
                          (check: any) => (
                            <div
                              key={check.ID}
                              className="border border-red-200 rounded-lg p-4 bg-red-50"
                            >
                              <div className="text-red-900">{check.Name}</div>
                            </div>
                          )
                        )}
                      </div>
                    </div>
                  )}
                </dd>
              </div>
            )}
            {item.results?.results?.https && (
              <div className="sm:col-span-4 px-2 pt-6">
                <div className="flex flex-row space-x-8 mb-4">
                  <dt className="text-sm font-medium text-gray-900">
                    HTTPS security
                  </dt>
                  <div className="flex gap-4">
                    <span className="inline-flex items-center rounded-full bg-green-100 px-2 text-xs font-medium text-green-800">
                      Passed: {item.results?.results?.https.data.Passed.length}
                    </span>
                    <span className="inline-flex items-center rounded-full bg-yellow-100 px-2 text-xs font-medium text-yellow-800">
                      Warnings:{" "}
                      {item.results?.results?.https.data.Warnings.length}
                    </span>
                    <span className="inline-flex items-center rounded-full bg-red-100 px-2 text-xs font-medium text-red-800">
                      Failed: {item.results?.results?.https.data.Failed.length}
                    </span>
                  </div>
                </div>
                <span className="text-gray-500 text-sm">
                  HTTPS security checks verify SSL certificate validity and
                  connection security
                </span>
                <dd className="mt-1">
                  <div className="mt-6">
                    <h4 className="text-sm font-medium text-gray-900 mb-3">
                      Passed security checks
                    </h4>
                    <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
                      {item.results?.results?.https.data.Passed.map(
                        (check: any) => (
                          <div
                            key={check.ID}
                            className="border rounded-lg p-4 bg-green-50"
                          >
                            <div className="text-gray-900">{check.Name}</div>
                            {check.Info && (
                              <div className="text-sm text-gray-600 mt-1">
                                {check.Info}
                              </div>
                            )}
                          </div>
                        )
                      )}
                    </div>
                  </div>
                  {item.results?.results?.https.data.Warnings.length > 0 && (
                    <div className="mt-6">
                      <h4 className="text-sm font-medium text-gray-900 mb-3">
                        Warnings
                      </h4>
                      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
                        {item.results?.results?.https.data.Warnings.map(
                          (check: any) => (
                            <div
                              key={check.ID}
                              className="border border-yellow-200 rounded-lg p-4 bg-yellow-50"
                            >
                              <div className="text-yellow-900">
                                {check.Name}
                              </div>
                              <div className="text-sm text-yellow-800 mt-1">
                                {check.Info}
                              </div>
                              {check.AdditionalInfo?.[0] && (
                                <div className="text-xs text-yellow-700 mt-1">
                                  {check.AdditionalInfo[0]}
                                </div>
                              )}
                            </div>
                          )
                        )}
                      </div>
                    </div>
                  )}
                  {item.results?.results?.https.data.Failed.length > 0 && (
                    <div className="mt-6">
                      <h4 className="text-sm font-medium text-gray-900 mb-3">
                        Failed security checks
                      </h4>
                      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
                        {item.results?.results?.https.data.Failed.map(
                          (check: any) => (
                            <div
                              key={check.ID}
                              className="border border-red-200 rounded-lg p-4 bg-red-50"
                            >
                              <div className="text-red-900">{check.Name}</div>
                              {check.Info && (
                                <div className="text-sm text-red-600 mt-1">
                                  {check.Info}
                                </div>
                              )}
                            </div>
                          )
                        )}
                      </div>
                    </div>
                  )}
                </dd>
              </div>
            )}
            {item.results?.results?.dns && (
              <div className="sm:col-span-4 px-2 pt-6">
                <div className="flex flex-row space-x-8 mb-4">
                  <dt className="text-sm font-medium text-gray-900">
                    DNS configuration
                  </dt>
                  <div className="flex gap-4">
                    <span className="inline-flex items-center rounded-full bg-green-100 px-2 text-xs font-medium text-green-800">
                      Passed: {item.results?.results?.dns.data.Passed.length}
                    </span>
                    <span className="inline-flex items-center rounded-full bg-yellow-100 px-2 text-xs font-medium text-yellow-800">
                      Warnings:{" "}
                      {item.results?.results?.dns.data.Warnings.length}
                    </span>
                    <span className="inline-flex items-center rounded-full bg-red-100 px-2 text-xs font-medium text-red-800">
                      Failed: {item.results?.results?.dns.data.Failed.length}
                    </span>
                  </div>
                </div>
                <span className="text-gray-500 text-sm">
                  DNS configuration checks verify nameserver setup and zone
                  configuration
                </span>
                <dd className="mt-1">
                  <div className="mt-6">
                    <h4 className="text-sm font-medium text-gray-900 mb-3">
                      Passed DNS checks
                    </h4>
                    <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
                      {item.results?.results?.dns.data.Passed.map(
                        (check: any) => (
                          <div
                            key={check.ID}
                            className="border rounded-lg p-4 bg-green-50"
                          >
                            <div className="text-gray-900">{check.Name}</div>
                            <div className="text-sm text-gray-600 mt-1">
                              {check.Info}
                            </div>
                            {check.AdditionalInfo?.[0] && (
                              <div className="text-xs text-gray-500 mt-1">
                                {check.AdditionalInfo[0]}
                              </div>
                            )}
                          </div>
                        )
                      )}
                    </div>
                  </div>

                  {item.results?.results?.dns.data.Warnings.length > 0 && (
                    <div className="mt-6">
                      <h4 className="text-sm font-medium text-gray-900 mb-3">
                        DNS configuration warnings
                      </h4>
                      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
                        {item.results?.results?.dns.data.Warnings.map(
                          (check: any) => (
                            <div
                              key={check.ID}
                              className="border border-yellow-200 rounded-lg p-4 bg-yellow-50"
                            >
                              <div className="text-yellow-900">
                                {check.Name}
                              </div>
                              <div className="text-sm text-yellow-800 mt-1">
                                {check.Info}
                              </div>
                              {check.AdditionalInfo?.[0] && (
                                <div className="text-xs text-yellow-700 mt-1">
                                  {check.AdditionalInfo[0]}
                                </div>
                              )}
                            </div>
                          )
                        )}
                      </div>
                    </div>
                  )}

                  {item.results?.results?.dns.data.Failed.length > 0 && (
                    <div className="mt-6">
                      <h4 className="text-sm font-medium text-gray-900 mb-3">
                        Failed DNS checks
                      </h4>
                      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
                        {item.results?.results?.dns.data.Failed.map(
                          (check: any) => (
                            <div
                              key={check.ID}
                              className="border border-red-200 rounded-lg p-4 bg-red-50"
                            >
                              <div className="text-red-900">{check.Name}</div>
                            </div>
                          )
                        )}
                      </div>
                    </div>
                  )}

                  {item.results?.results?.dns.data.Information.length > 0 && (
                    <div className="mt-6">
                      <h4 className="text-sm font-medium text-gray-900 mb-3">
                        DNS nameservers
                      </h4>
                      <div className="overflow-x-auto">
                        <table className="min-w-full divide-y divide-gray-300">
                          <thead className="bg-gray-50">
                            <tr>
                              <th className="px-3 py-3.5 text-left text-sm font-semibold text-gray-900">
                                Domain Name
                              </th>
                              <th className="px-3 py-3.5 text-left text-sm font-semibold text-gray-900">
                                IP Address
                              </th>
                              <th className="px-3 py-3.5 text-left text-sm font-semibold text-gray-900">
                                TTL
                              </th>
                              <th className="px-3 py-3.5 text-left text-sm font-semibold text-gray-900">
                                Response Time
                              </th>
                            </tr>
                          </thead>
                          <tbody className="divide-y divide-gray-200 bg-white">
                            {item.results?.results?.dns.data.Information.map(
                              (info: any, index: number) => (
                                <tr key={index}>
                                  <td className="whitespace-nowrap print:whitespace-normal px-3 py-4 text-sm text-gray-900">
                                    {info["Domain Name"]}
                                  </td>
                                  <td className="whitespace-nowrap print:whitespace-normal px-3 py-4 text-sm text-gray-500">
                                    {info["IP Address"]}
                                  </td>
                                  <td className="whitespace-nowrap print:whitespace-normal px-3 py-4 text-sm text-gray-500">
                                    {info["TTL"]}
                                  </td>
                                  <td className="whitespace-nowrap print:whitespace-normal px-3 py-4 text-sm text-gray-500">
                                    {info["Time (ms)"]} ms
                                  </td>
                                </tr>
                              )
                            )}
                          </tbody>
                        </table>
                      </div>
                    </div>
                  )}
                </dd>
              </div>
            )}
          </dl>
        </div>
      )}
      {item.status === "complete" ? (
        <Chat chat_id={chat_id} checkup_id={checkup_id} check_id={check_id} />
      ) : (
        <div className="w-full mt-4">
          <p className="text-sm text-gray-500">
            Chat will be avaliable after completing the check
          </p>
        </div>
      )}
    </div>
  );
}
