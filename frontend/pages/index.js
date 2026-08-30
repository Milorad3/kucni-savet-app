import { useEffect } from "react";
import { useRouter } from "next/router";
import { isLoggedIn } from "../lib/api";

export default function Home() {
  const router = useRouter();

  useEffect(() => {
    router.replace(isLoggedIn() ? "/dashboard" : "/login");
  }, []);

  return null;
}
