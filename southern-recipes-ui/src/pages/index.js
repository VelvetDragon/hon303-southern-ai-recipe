// pages/index.js
import Link from "next/link";
import Head from "next/head";

export default function Home() {
  return (
    <>
      <Head>
        <title>AI Southern Recipes Research</title>
      </Head>
      <main style={{ padding: "2rem", fontFamily: "sans-serif" }}>
        <h1 style={{ fontFamily: "serif", color: "#2F4F4F" }}>
          AI-Generated Southern Recipes
        </h1>
        <p>Research project on machine learning and Southern cuisine.</p>{" "}
        <Link href="/recipes" style={{ color: "#C75B12", fontWeight: "bold" }}>
           → Go to Recipe Finder {" "}
        </Link>
      </main>
    </>
  );
}
