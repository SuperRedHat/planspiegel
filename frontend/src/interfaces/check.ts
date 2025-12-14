export interface ICheck {
  check_id: string;
  check_type: string;
  status: string;
  results: unknown;
  results_description: unknown;
  chat?: {
    chat_id: string;
    check_id: string;
    messages: unknown[];
  }
}

export interface IStep {
  name: string;
  status: "upcoming" | "current" | "complete" | "failed";
  href: string;
  tag: string;

  check_id?: string;
  checkup_id?: string;
  check_type?: string;
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  results?: any;
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  results_description?: any;
  chat?: {
    chat_id: string;
    check_id: string;
    messages: unknown[];
  }
}
