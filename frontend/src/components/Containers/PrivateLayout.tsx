import { ReactNode, useState } from "react";
import {
  Dialog,
  DialogBackdrop,
  DialogPanel,
  TransitionChild,
} from "@headlessui/react";
import {
  Bars3Icon,
  PlusCircleIcon,
  XMarkIcon,
} from "@heroicons/react/24/outline";
import { IoLogOut } from "react-icons/io5";
import { classNames } from "@app/utils/helpers";
import logo from "@app/assets/Planspiegel.svg";
import { useUserClaimsQuery } from "@app/state/user";
import API from "@app/api/api";
import { toast } from "react-toastify";
import { useNavigate } from "react-router-dom";
import { useQuery, useQueryClient } from "@tanstack/react-query";

function PrivateLayout({ children }: { children: ReactNode }) {
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [selectedCheckup, setSelectedCheckup] = useState<string | null>(null);
  const userClaims = useUserClaimsQuery();
  const QueryClient = useQueryClient();

  const { data: checkupsList = [] } = useQuery({
    queryKey: ['checkups'],
    queryFn: () => API.chat.getList().then(res => res.data)
  });

  const navigate = useNavigate();

  function extractDomain(url: string) {
    try{
      const hostname = new URL(url).hostname; //Extracts domain
      return hostname.replace(/^www\./,""); //remove 'WWW'
    }
    catch(error: unknown) {
      console.log(error);
      return url;
    }
  }

  return (
    <div className="w-full h-full">
      <Dialog
        open={sidebarOpen}
        onClose={setSidebarOpen}
        className="relative z-50 lg:hidden"
      >
        <DialogBackdrop
          transition
          className="fixed inset-0 bg-gray-900/80 transition-opacity duration-300 ease-linear data-[closed]:opacity-0"
        />

        <div className="fixed inset-0 flex">
          <DialogPanel
            transition
            className="relative mr-16 flex w-full max-w-xs flex-1 transform transition duration-300 ease-in-out data-[closed]:-translate-x-full"
          >
            <TransitionChild>
              <div className="absolute left-full top-0 flex w-16 justify-center pt-5 duration-300 ease-in-out data-[closed]:opacity-0">
                <button
                  type="button"
                  onClick={() => setSidebarOpen(false)}
                  className="-m-2.5 p-2.5 bg-sky-500 hover:bg-sky-600"
                >
                  <span className="sr-only">Close sidebar</span>
                  <XMarkIcon aria-hidden="true" className="size-6 text-white" />
                </button>
              </div>
            </TransitionChild>
            {/* Sidebar component, swap this element with another sidebar if you like */}
            <div className="flex grow flex-col gap-y-5 overflow-y-auto bg-white px-6 pb-2">
              <div className="contents md:flex sm:h-24 h-16 shrink-0 items-center sm:justify-center">
                <img alt="Planspiegel" src={logo} className="h-40 w-auto" />
              </div>
              <nav className="flex flex-1 flex-col">
                <ul role="list" className="flex flex-1 flex-col ">
                  <li>
                    <a
                      href="/checkup/new"
                      className={
                        "text-sky-50 mb-3 hover:text-white flex flex-row justify-start items-center h-10 bg-sky-400 hover:bg-sky-500 group gap-x-3 rounded-md py-2 px-4 text-sm/6 font-semibold"
                      }
                    >
                      <PlusCircleIcon className="size-6 font-medium" />
                      <span>Add URL</span>
                    </a>
                  </li>
                  <li>
                    <ul role="list" className="-mx-2 space-y-1 max-h-[22rem]
                            sm:max-h-[14rem]
                            md:max-h-[22rem] overflow-y-auto">

                      {checkupsList.map(
                        (item: { url: string; checkup_id: string }) => (
                          <li key={item.url}>
                            <a
                              href={`/checkup/${item.checkup_id}`}
                              onClick={() =>
                                setSelectedCheckup(item.checkup_id)
                              }
                              className={classNames(
                                item.checkup_id === selectedCheckup
                                  ? "bg-gray-50 text-sky-600"
                                  : "text-gray-700 hover:bg-gray-50 hover:text-sky-600",
                                "group flex gap-x-3 rounded-md p-2 text-sm/6 font-semibold"
                              )}
                            >
                              {extractDomain(item.url)}
                            </a>
                          </li>
                        )
                      )}
                    </ul>
                  </li>
                  <li className="mt-auto flex items-center justify-center w-full">
                <div className="flex w-full items-center gap-x-2 px-2 py-3 text-sm/6 font-semibold text-gray-900">
                  <span className="sr-only">Your profile</span>
                  <span
                    aria-hidden="true"
                    className="text-xs truncate max-w-[200px]"
                  >
                    {userClaims.data?.user.email || "loading..."}
                  </span>
                  <button
                    className="bg-sky-500 hover:bg-sky-600 ml-auto border-0 text-white"
                    onClick={() => {
                      API.auth.logout().then(() => {
                        QueryClient.invalidateQueries();
                        navigate("/login");
                        toast.info("Successfully log out");
                      });
                    }}
                  >
                    <IoLogOut />
                  </button>
                </div>
              </li>
                </ul>
              </nav>
            </div>
          </DialogPanel>
        </div>
      </Dialog>

      {/* Static sidebar for desktop */}
      <div className="hidden lg:fixed lg:inset-y-0 lg:z-50 lg:flex lg:w-72 lg:flex-col">
        {/* Sidebar component, swap this element with another sidebar if you like */}
        <div className="flex grow flex-col gap-y-5 overflow-y-auto border-r border-gray-200 bg-white px-6">
          <div className="flex h-28 w-full shrink-0 items-center justify-center">
            <a href="/">
              <img alt="Planspiegel" src={logo} className="h-28" />
            </a>
          </div>
          <nav className="flex flex-1 flex-col">
            <ul role="list" className="flex flex-1 flex-col ">
              <li>
                <a
                  href="/checkup/new"
                  className={
                    "text-sky-50 mb-3 hover:text-white flex flex-row justify-start items-center h-10 bg-sky-400 hover:bg-sky-500 group gap-x-3 rounded-md py-2 px-4 text-sm/6 font-semibold"
                  }
                >
                  <PlusCircleIcon className="size-6 font-medium" />
                  <span>Add URL</span>
                </a>
              </li>
              <li>
                <ul role="list" className="-mx-2 space-y-1 max-h-[18rem]
                            md:max-h-[22rem]
                            lg:max-h-[22rem]
                            xl:max-h-[42rem]
                            2xl:max-h-[50rem] overflow-y-auto">

                  {checkupsList.map(
                    (item: { url: string; checkup_id: string }) => (
                      <li key={item.url}>
                        <a
                          href={`/checkup/${item.checkup_id}`}
                          onClick={() => setSelectedCheckup(item.checkup_id)}
                          className={classNames(
                            item.checkup_id === selectedCheckup
                              ? "bg-sky-100 text-sky-600"
                              : "text-gray-700 hover:bg-sky-50 hover:text-sky-600",
                            "group flex gap-x-3 rounded-md py-2 px-4 text-sm/6 font-semibold break-all"                          )}
                        >
                          {extractDomain(item.url)}
                        </a>
                      </li>
                    )
                  )}
                </ul>
              </li>
              <li className="mt-auto flex items-center justify-center w-full">
                <div className="flex w-full items-center gap-x-2 px-2 py-3 text-sm/6 font-semibold text-gray-900">
                  <span className="sr-only">Your profile</span>
                  <span
                    aria-hidden="true"
                    className="text-xs truncate max-w-[200px]"
                  >
                    {userClaims.data?.user.email || "loading..."}
                  </span>
                  <button
                    className="bg-sky-500 hover:bg-sky-600 ml-auto border-0 text-white"
                    onClick={() => {
                      API.auth.logout().then(() => {
                        QueryClient.invalidateQueries();
                        navigate("/login");
                        toast.info("Successfully log out");
                      });
                    }}
                  >
                    <IoLogOut />
                  </button>
                </div>
              </li>
            </ul>
          </nav>
        </div>
      </div>

      <div className="sticky top-0 z-40 flex items-center gap-x-6 bg-white px-4 py-4 shadow-sm sm:px-6 lg:hidden print:hidden">
        <button
          type="button"
          onClick={() => setSidebarOpen(true)}
          className="-m-2.5 p-2.5 bg-sky-500 hover:bg-sky-600 text-white lg:hidden"
        >
          <span className="sr-only">Open sidebar</span>
          <Bars3Icon aria-hidden="true" className="size-6" />
        </button>
        <div className="flex-1 text-sm/6 font-semibold text-gray-900">
          Dashboard
        </div>
        <a href="#">
          <span className="sr-only">Your profile</span>
        </a>
      </div>

      <main className="py-10 lg:pl-72 w-full h-full">{children}</main>
    </div>
  );
}

export default PrivateLayout;
