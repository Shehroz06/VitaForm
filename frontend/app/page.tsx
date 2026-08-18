import { PublicNavbar } from "@/components/navbar/PublicNavbar";
import { Hero } from "@/components/marketing/Hero";
import { ValueSection } from "@/components/marketing/ValueSection";
import { TemplatesPreview } from "@/components/marketing/TemplatesPreview";
import { HowItWorks } from "@/components/marketing/HowItWorks";
import { FeaturesSection } from "@/components/marketing/FeaturesSection";
import { AboutSection } from "@/components/marketing/AboutSection";
import { FinalCta } from "@/components/marketing/FinalCta";
import { Footer } from "@/components/marketing/Footer";

export default function Home() {
  return (
    <div className="flex flex-1 flex-col">
      <PublicNavbar />
      <main className="flex flex-1 flex-col">
        <Hero />
        <ValueSection />
        <TemplatesPreview />
        <HowItWorks />
        <FeaturesSection />
        <AboutSection />
        <FinalCta />
      </main>
      <Footer />
    </div>
  );
}
