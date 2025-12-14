import API from "@app/api/api";
import PrivateLayout from "@app/components/Containers/PrivateLayout";
import URLChecksList from "@app/components/URLChecksList";
import {
  CheckCircleIcon,
  PaperClipIcon,
  XCircleIcon,
} from "@heroicons/react/20/solid";
import { useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import * as _ from "lodash";
import { ICheck, IStep } from "@app/interfaces/check";
import { useQuery, useQueryClient } from "@tanstack/react-query";

export default function URLPage() {
  const queryClient = useQueryClient();
  const [url, setUrl] = useState("");
  const [isAllCompleted, setIsAllCompleted] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const initialSteps: IStep[] = [
    {
      name: "Deprecated technologies and CVE",
      status: "upcoming",
      href: "#technologies",
      tag: "technologies",
    },
    {
      name: "Cookies and GDPR compliance",
      status: "upcoming",
      href: "#cookie",
      tag: "cookie",
    },
    {
      name: "Open ports scanning",
      status: "upcoming",
      href: "#scan_ports",
      tag: "scan_ports",
    },
    {
      name: "Lighthouse",
      status: "upcoming",
      href: "#lighthouse",
      tag: "lighthouse",
    },
    {
      name: "Network",
      status: "upcoming",
      href: "#network",
      tag: "network",
    },
  ];
  const [steps, setSteps] = useState<IStep[]>(initialSteps);
  const { checkup_id } = useParams();

  const checkupsData = useQuery({
    queryKey: ["checkup", checkup_id],
    queryFn: () => {
      if (checkup_id)
        return API.chat.getCheckup(checkup_id).then((res) => {
          return res.data;
        });
    },
    enabled: !!checkup_id && checkup_id !== "new",
    refetchInterval: (data) => {
      // fetch every 5 seconds, if all done, stop
      if (!data?.state?.data) return 5000;

      const allChecksCompleted = data.state.data.checks?.every(
        (check: ICheck) =>
          check.status === "completed" || check.status === "failed"
      );

      return allChecksCompleted ? false : 5000;
    },
  });

  const navigate = useNavigate();

  useEffect(() => {
    if (checkupsData.data) {
      setUrl(checkupsData.data.url);

      const lighthouse: ICheck = _.filter(checkupsData.data.checks, (check) => {
        return check.check_type === "lighthouse";
      })[0];

      const technologies: ICheck = _.filter(
        checkupsData.data.checks,
        (check) => {
          return check.check_type === "technologies";
        }
      )[0];

      const cookie: ICheck = _.filter(checkupsData.data.checks, (check) => {
        return check.check_type === "cookie";
      })[0];

      const scan_ports: ICheck = _.filter(checkupsData.data.checks, (check) => {
        return check.check_type === "scan_ports";
      })[0];

      const network: ICheck = _.filter(checkupsData.data.checks, (check) => {
        return check.check_type === "network";
      })[0];

      setIsAllCompleted(
        checkupsData.data.checks?.every(
          (check: ICheck) =>
            check.status === "completed" || check.status === "failed"
        )
      );

      setSteps((prev) =>
        prev.map((step) => {
          if (step.tag === "lighthouse") {
            return {
              ...step,
              ...lighthouse,
              checkup_id: checkupsData.data.checkup_id,
              status:
                lighthouse.status === "completed"
                  ? "complete"
                  : lighthouse.status === "failed"
                  ? "failed"
                  : "current",
            };
          }
          if (step.tag === "network") {
            return {
              ...step,
              ...network,
              checkup_id: checkupsData.data.checkup_id,
              status:
                network?.status === "completed"
                  ? "complete"
                  : network?.status === "failed"
                  ? "failed"
                  : "current",
            };
          }
          if (step.tag === "technologies") {
            return {
              ...step,
              ...technologies,
              checkup_id: checkupsData.data.checkup_id,
              status:
                technologies.status === "completed"
                  ? "complete"
                  : technologies.status === "failed"
                  ? "failed"
                  : "current",
            };
          }
          if (step.tag === "cookie") {
            return {
              ...step,
              ...cookie,
              checkup_id: checkupsData.data.checkup_id,
              status:
                cookie.status === "completed"
                  ? "complete"
                  : cookie.status === "failed"
                  ? "failed"
                  : "current",
            };
          }
          if (step.tag === "scan_ports") {
            return {
              ...step,
              ...scan_ports,
              checkup_id: checkupsData.data.checkup_id,
              status:
                scan_ports.status === "completed"
                  ? "complete"
                  : scan_ports.status === "failed"
                  ? "failed"
                  : "current",
            };
          }
          return step;
        })
      );
    }
  }, [checkupsData.data]);

  const handleDownloadReport = () => window.print();

  return (
    <PrivateLayout>
      <div className="px-4 sm:px-6 lg:px-8 flex flex-col w-full justify-start overflow-y-auto">
        <div className="overflow-x-hidden bg-white min-h-20 px-4 py-4 shadow print:shadow-none sm:rounded-md sm:px-6 flex flex-col">
          <h2 className="text-lg font-medium leading-6 text-gray-900 mb-4 print:hidden">
            Setup
          </h2>
          <div className="w-full flex flex-row space-x-2">
            <input
              id="website-url"
              name="website-url"
              value={url}
              onChange={(e) => setUrl(e.target.value)}
              type="text"
              placeholder="https://www.example.com"
              aria-label="Website URL"
              className="block w-full rounded-md bg-white px-3 py-1.5 text-base text-gray-900 outline outline-1 -outline-offset-1 outline-gray-300 print:outline-none placeholder:text-gray-400 focus:outline focus:outline-2 focus:-outline-offset-2 focus:outline-sky-600 sm:text-sm/6 print:border-none"
            />
            <button
              type="submit"
              className="w-[220px] p-3 bg-sky-500 hover:bg-sky-600 text-white border-0 disabled:bg-gray-600 disabled:cursor-not-allowed print:hidden"
              onClick={() => {
                setIsLoading(true);
                API.chat.startCheckup(url).then((res) => {
                  queryClient.invalidateQueries({ queryKey: ["checkups"] });
                  setIsLoading(false);
                  navigate(`/checkup/${res.data.checkup_id}`);
                });
              }}
              disabled={isLoading}
            >
              Start check
            </button>
          </div>
          <div className="mt-4 flex flex-col w-full items-start">
            <div className="flex flex-col w-full py-4 items-start">
              <h3 className="text-base font-medium leading-6 text-gray-700 mb-4">
                Status
              </h3>
              <nav aria-label="Progress" className="flex justify-center">
                <ol role="list" className="space-y-6">
                  {steps.map((step) => (
                    <li key={step.name}>
                      {step.status === "complete" ? (
                        <div className="group">
                          <a
                            href={step.href}
                            className="flex items-start cursor-pointer"
                          >
                            <span className="relative flex size-5 shrink-0 items-center justify-center">
                              <CheckCircleIcon
                                aria-hidden="true"
                                className="size-full text-sky-500 group-hover:text-sky-600"
                              />
                            </span>
                            <span className="ml-3 text-sm font-medium text-gray-500 group-hover:text-gray-900">
                              {step.name}
                            </span>
                          </a>
                        </div>
                      ) : step.status === "current" ? (
                        <a
                          href={step.href}
                          aria-current="step"
                          className="flex items-start cursor-pointer"
                        >
                          <span
                            aria-hidden="true"
                            className="relative flex size-5 shrink-0 items-center justify-center"
                          >
                            <span className="absolute size-4 rounded-full bg-sky-200 pulse-animation" />
                            <span className="relative block size-2 rounded-full bg-sky-600" />
                          </span>
                          <span className="ml-3 text-sm font-medium text-sky-600">
                            {step.name}
                          </span>
                        </a>
                      ) : step.status === "failed" ? (
                        <div className="group flex flex-col w-full">
                          <a
                            href={step.href}
                            className="flex items-start cursor-pointer"
                          >
                            <span className="relative flex size-5 shrink-0 items-center justify-center">
                              <XCircleIcon
                                aria-hidden="true"
                                className="size-full text-red-500 group-hover:text-red-600"
                              />
                            </span>
                            <span className="ml-3 text-sm font-medium text-red-500 group-hover:text-red-600">
                              {step.name}
                            </span>
                          </a>
                          {step.results?.exception && (
                            <span className="mt-3 py-1 px-2 bg-red-50 rounded-md text-red-800">
                              {step.results.exception}
                            </span>
                          )}
                        </div>
                      ) : (
                        <div className="group">
                          <a
                            href={step.href}
                            className="flex items-start cursor-pointer"
                          >
                            <span
                              aria-hidden="true"
                              className="relative flex size-5 shrink-0 items-center justify-center"
                            >
                              <div className="size-2 rounded-full bg-gray-300 group-hover:bg-gray-400" />
                            </span>
                            <p className="ml-3 text-sm font-medium text-gray-500 group-hover:text-gray-900">
                              {step.name}
                            </p>
                          </a>
                        </div>
                      )}
                    </li>
                  ))}
                </ol>
              </nav>
            </div>

            {checkup_id && checkup_id !== "new" && isAllCompleted && (
              <div className="flex flex-col w-full py-4 border-t border-b border-gray-200 print:hidden">
                <h3 className="text-base font-medium leading-6 text-gray-700 mb-4">
                  Report
                </h3>
                <ul
                  role="list"
                  className="divide-y w-full divide-gray-200 rounded-md border border-gray-200"
                >
                  <li className="flex items-center justify-between py-3 pl-3 pr-4 text-sm">
                    <div className="flex w-0 flex-1 items-center">
                      <PaperClipIcon
                        aria-hidden="true"
                        className="size-5 shrink-0 text-gray-400"
                      />
                      <span className="ml-2 w-0 flex-1 truncate">
                        Report.pdf
                      </span>
                    </div>
                    <div className="ml-4 shrink-0">
                      <button
                        onClick={handleDownloadReport}
                        className="font-medium text-white text-xs cursor-pointer hover:text-white bg-sky-500 outline-none h-full px-3 py-1.5 rounded-md hover:bg-sky-600"
                      >
                        Download
                      </button>
                    </div>
                  </li>
                </ul>
              </div>
            )}
          </div>
        </div>

        <URLChecksList steps={steps} />
      </div>
    </PrivateLayout>
  );
}
