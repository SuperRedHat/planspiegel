export interface IUserData {
  _id?: string;
  email: string;
  password: string;
  status: "active" | "deleted";
  userType: "regular" | "pro";
  providers?: string[];
}

export interface ILoginData {
  email: string;
  password: string;
}
