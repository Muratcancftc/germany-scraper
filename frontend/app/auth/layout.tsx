import { Metadata } from "next";

export const metadata: Metadata = {
  title: "Login - Germany Scraper",
};

export default function LoginLayout({ children }: { children: React.ReactNode }) {
  return <>{children}</>;
}
