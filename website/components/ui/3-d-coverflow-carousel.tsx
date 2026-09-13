"use client";

import React, { useState, useEffect, useCallback, useRef } from "react";
import Link from "next/link";

// 3D cover-flow carousel. Adapted for Imperium Detailing: brand colours, signed
// offsets so small sets stay balanced, a compact layout for phones, keyboard
// control scoped to the stage, and 24px touch targets on the dots.

const ChevronLeftIcon = () => (
  <svg width="20" height="20" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5} aria-hidden="true">
    <path strokeLinecap="round" strokeLinejoin="round" d="M15 19l-7-7 7-7" />
  </svg>
);

const ChevronRightIcon = () => (
  <svg width="20" height="20" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5} aria-hidden="true">
    <path strokeLinecap="round" strokeLinejoin="round" d="M9 5l7 7-7 7" />
  </svg>
);

export interface CarouselItem {
  tag?: string;
  titleLine1: string;
  titleLine2?: string;
  desc?: string;
  img: string;
  imgSrcSet?: string;
  imgAlt?: string;
  /** Optional loop shown instead of the photo; it only plays on the centre card. */
  video?: { mp4: string; webm?: string; poster: string };
  ctaText?: string;
  ctaUrl?: string;
}

export interface CoverFlowCarouselProps {
  items: CarouselItem[];
  sectionLabel?: string;
  autoplay?: boolean;
  autoplayDelay?: number;
  className?: string;
  onCtaClick?: (item: CarouselItem) => void;
}

const ACCENT = "#3a8fe0";
const BG = "#050608";

export function CoverFlowCarousel({
  items,
  sectionLabel,
  autoplay = true,
  autoplayDelay = 5000,
  className = "",
  onCtaClick,
}: CoverFlowCarouselProps) {
  const [currentIndex, setCurrentIndex] = useState(0);
  const [isHovered, setIsHovered] = useState(false);
  const [compact, setCompact] = useState(false);
  const [reduceMotion, setReduceMotion] = useState(false);
  const touchStartX = useRef(0);
  const videoRefs = useRef<Record<number, HTMLVideoElement | null>>({});
  const total = items.length;

  // Only the centre card moves; the rest sit on their posters.
  useEffect(() => {
    Object.entries(videoRefs.current).forEach(([i, v]) => {
      if (!v) return;
      if (Number(i) === currentIndex && !reduceMotion) v.play().catch(() => {});
      else v.pause();
    });
  }, [currentIndex, reduceMotion]);

  const nextSlide = useCallback(() => setCurrentIndex((prev) => (prev + 1) % total), [total]);
  const prevSlide = useCallback(() => setCurrentIndex((prev) => (prev - 1 + total) % total), [total]);
  const goToSlide = (idx: number) => setCurrentIndex(((idx % total) + total) % total);

  useEffect(() => {
    const mq = window.matchMedia("(max-width: 719px)");
    const rm = window.matchMedia("(prefers-reduced-motion: reduce)");
    const apply = () => {
      setCompact(mq.matches);
      setReduceMotion(rm.matches);
    };
    apply();
    mq.addEventListener("change", apply);
    rm.addEventListener("change", apply);
    return () => {
      mq.removeEventListener("change", apply);
      rm.removeEventListener("change", apply);
    };
  }, []);

  useEffect(() => {
    if (!autoplay || isHovered || reduceMotion || total <= 1) return;
    const interval = setInterval(nextSlide, autoplayDelay);
    return () => clearInterval(interval);
  }, [autoplay, autoplayDelay, isHovered, reduceMotion, nextSlide, total]);

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "ArrowLeft") {
      e.preventDefault();
      prevSlide();
    }
    if (e.key === "ArrowRight") {
      e.preventDefault();
      nextSlide();
    }
  };

  const handleTouchStart = (e: React.TouchEvent) => {
    touchStartX.current = e.touches[0].clientX;
  };

  const handleTouchEnd = (e: React.TouchEvent) => {
    const diff = e.changedTouches[0].clientX - touchStartX.current;
    if (Math.abs(diff) > 45) {
      if (diff < 0) nextSlide();
      else prevSlide();
    }
  };

  if (!items || items.length === 0) return null;

  // Geometry for the two layouts.
  const card = compact ? { w: 250, h: 380 } : { w: 330, h: 500 };
  const near = compact ? 180 : 285;
  const far = compact ? 320 : 510;
  const stageH = compact ? 420 : 540;
  const transition = reduceMotion ? "none" : "all 800ms cubic-bezier(0.25, 1, 0.5, 1)";

  return (
    <section
      className={`relative w-full flex items-center justify-center overflow-hidden py-10 select-none ${className}`}
      style={{ backgroundColor: BG, color: "#f3f5f8" }}
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
      onTouchStart={handleTouchStart}
      onTouchEnd={handleTouchEnd}
      aria-roledescription="carousel"
      aria-label={sectionLabel ? `${sectionLabel} carousel` : "Carousel"}
    >
      {/* Background ambience: the current photo, blurred. */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none z-0" aria-hidden="true">
        <img
          src={items[currentIndex]?.img}
          alt=""
            width={480}
            height={640}
            loading="lazy"
            decoding="async"
          style={{
            width: "100%",
            height: "100%",
            objectFit: "cover",
            filter: "brightness(0.22) blur(32px)",
            transform: "scale(1.15)",
            transition: reduceMotion ? "none" : "opacity 1000ms ease, filter 1000ms ease",
          }}
        />
        <div
          className="absolute inset-0"
          style={{ background: "radial-gradient(circle at center, rgba(5,6,8,0.3) 0%, rgba(5,6,8,0.94) 100%)" }}
        />
      </div>

      <div className="relative w-full max-w-6xl mx-auto px-4 z-10 flex flex-col items-center">
        {sectionLabel && (
          <p className="mb-6 text-sm text-[#8a909a]" style={{ margin: "0 0 24px" }}>
            {sectionLabel}
          </p>
        )}

        {/* 3D stage */}
        <div
          className="relative w-full flex justify-center items-center mb-6 outline-none"
          style={{ perspective: "1400px", height: `${stageH}px` }}
          tabIndex={0}
          onKeyDown={handleKeyDown}
          aria-live="polite"
        >
          {items.map((item, idx) => {
            // Signed offset: -2, -1, 0, 1, 2 around the centre, whatever the set size.
            let off = (idx - currentIndex + total) % total;
            if (off > total / 2) off -= total;

            let transform = "translateX(0px) scale(0.4) rotateY(0deg)";
            let opacity = 0;
            let zIndex = 0;
            let filter = "brightness(0.4) blur(2px)";
            const isCenter = off === 0;

            if (off === 0) {
              transform = "translateX(0px) scale(1) rotateY(0deg)";
              opacity = 1;
              zIndex = 30;
              filter = "brightness(1)";
            } else if (off === 1) {
              transform = `translateX(${near}px) scale(0.84) rotateY(-24deg)`;
              opacity = 0.65;
              zIndex = 20;
              filter = "brightness(0.75)";
            } else if (off === 2) {
              transform = `translateX(${far}px) scale(0.68) rotateY(-38deg)`;
              opacity = 0.38;
              zIndex = 10;
              filter = "brightness(0.55) blur(1px)";
            } else if (off === -1) {
              transform = `translateX(-${near}px) scale(0.84) rotateY(24deg)`;
              opacity = 0.65;
              zIndex = 20;
              filter = "brightness(0.75)";
            } else if (off === -2) {
              transform = `translateX(-${far}px) scale(0.68) rotateY(38deg)`;
              opacity = 0.38;
              zIndex = 10;
              filter = "brightness(0.55) blur(1px)";
            }

            return (
              <div
                key={idx}
                onClick={() => !isCenter && goToSlide(idx)}
                aria-hidden={!isCenter}
                style={{
                  position: "absolute",
                  width: `${card.w}px`,
                  height: `${card.h}px`,
                  borderRadius: "16px",
                  overflow: "hidden",
                  backgroundColor: "#0c0f14",
                  border: "1px solid rgba(194, 200, 208, 0.14)",
                  transform,
                  opacity,
                  zIndex,
                  filter,
                  transformOrigin: "center center",
                  transition,
                  boxShadow: isCenter
                    ? "0 25px 60px rgba(0,0,0,0.9), 0 0 40px rgba(58,143,224,0.22)"
                    : "0 15px 35px rgba(0,0,0,0.5)",
                  cursor: isCenter ? "default" : "pointer",
                }}
              >
                {item.video ? (
                  <video
                    ref={(el) => {
                      videoRefs.current[idx] = el;
                    }}
                    muted
                    loop
                    playsInline
                    preload="none"
                    poster={item.video.poster}
                    aria-label={item.imgAlt ?? item.titleLine1}
                    style={{ position: "absolute", inset: 0, width: "100%", height: "100%", objectFit: "cover" }}
                  >
                    {item.video.webm && <source src={item.video.webm} type="video/webm" />}
                    <source src={item.video.mp4} type="video/mp4" />
                  </video>
                ) : (
                  <img
                    src={item.img}
                    srcSet={item.imgSrcSet}
                    sizes={`${card.w}px`}
                    alt={item.imgAlt ?? item.titleLine1}
                    loading="lazy"
                    decoding="async"
                    style={{ position: "absolute", inset: 0, width: "100%", height: "100%", objectFit: "cover" }}
                  />
                )}

                <div
                  style={{
                    position: "absolute",
                    inset: 0,
                    background: "linear-gradient(180deg, rgba(0,0,0,0.35) 0%, rgba(0,0,0,0.08) 25%, rgba(0,0,0,0.66) 60%, rgba(5,6,8,0.96) 100%)",
                    pointerEvents: "none",
                    zIndex: 10,
                  }}
                />

                <div
                  style={{
                    position: "relative",
                    width: "100%",
                    height: "100%",
                    padding: compact ? "16px 14px 18px" : "20px 18px 22px",
                    display: "flex",
                    flexDirection: "column",
                    justifyContent: "space-between",
                    textAlign: "center",
                    zIndex: 20,
                    opacity: isCenter ? 1 : 0,
                    transform: isCenter ? "translateY(0px)" : "translateY(16px)",
                    transition: reduceMotion ? "none" : "opacity 500ms ease, transform 500ms ease",
                    pointerEvents: isCenter ? "auto" : "none",
                  }}
                >
                  <div style={{ textAlign: "right", width: "100%", paddingRight: "4px" }}>
                    {item.tag && (
                      <span
                        style={{
                          display: "inline-block",
                          fontSize: "0.8rem",
                          fontWeight: 600,
                          color: "rgba(243,245,248,0.92)",
                          textShadow: "0 2px 6px rgba(0,0,0,0.8)",
                        }}
                      >
                        {item.tag}
                      </span>
                    )}
                  </div>

                  <div style={{ display: "flex", flexDirection: "column", alignItems: "center", gap: "3px", marginTop: "auto", paddingBottom: "4px" }}>
                    <h3
                      className="display"
                      style={{
                        fontSize: compact ? "1.7rem" : "2.1rem",
                        color: "#f3f5f8",
                        margin: 0,
                        lineHeight: 1,
                        textShadow: "0 3px 12px rgba(0,0,0,0.95)",
                      }}
                    >
                      {item.titleLine1}
                    </h3>

                    {item.titleLine2 && (
                      <span
                        style={{
                          fontSize: "0.95rem",
                          fontWeight: 500,
                          color: "#c2c8d0",
                          lineHeight: 1.3,
                          textShadow: "0 3px 10px rgba(0,0,0,0.9)",
                        }}
                      >
                        {item.titleLine2}
                      </span>
                    )}

                    <div
                      style={{
                        width: "34px",
                        height: "2px",
                        backgroundColor: ACCENT,
                        borderRadius: "2px",
                        margin: "8px auto 6px",
                        boxShadow: "0 0 8px rgba(58,143,224,0.7)",
                      }}
                    />

                    {item.desc && (
                      <p
                        style={{
                          fontSize: "0.86rem",
                          color: "rgba(243,245,248,0.88)",
                          maxWidth: "280px",
                          margin: "0 0 12px",
                          lineHeight: 1.35,
                          textShadow: "0 2px 8px rgba(0,0,0,0.9)",
                        }}
                      >
                        {item.desc}
                      </p>
                    )}

                    <Link
                      href={item.ctaUrl || "#"}
                      tabIndex={isCenter ? 0 : -1}
                      onClick={(e) => {
                        if (onCtaClick) {
                          e.preventDefault();
                          onCtaClick(item);
                        }
                      }}
                      style={{
                        display: "inline-flex",
                        alignItems: "center",
                        justifyContent: "center",
                        minHeight: "44px",
                        padding: "10px 20px",
                        borderRadius: "8px",
                        background: `linear-gradient(135deg, ${ACCENT} 0%, #1f6fc4 100%)`,
                        color: "#050608",
                        fontSize: "0.9rem",
                        fontWeight: 600,
                        textDecoration: "none",
                        boxShadow: "0 4px 14px rgba(0,0,0,0.4), 0 0 15px rgba(58,143,224,0.3)",
                      }}
                    >
                      {item.ctaText || "See what's included"}
                    </Link>
                  </div>
                </div>
              </div>
            );
          })}
        </div>

        {/* Arrows */}
        <button
          type="button"
          onClick={prevSlide}
          aria-label="Previous service"
          className="absolute top-1/2 -translate-y-1/2 left-2 md:left-6 z-40 flex items-center justify-center w-12 h-12 rounded-full text-white cursor-pointer"
          style={{ backgroundColor: "rgba(5,6,8,0.6)", border: "1px solid rgba(255,255,255,0.2)", backdropFilter: "blur(8px)", boxShadow: "0 8px 24px rgba(0,0,0,0.4)" }}
        >
          <ChevronLeftIcon />
        </button>
        <button
          type="button"
          onClick={nextSlide}
          aria-label="Next service"
          className="absolute top-1/2 -translate-y-1/2 right-2 md:right-6 z-40 flex items-center justify-center w-12 h-12 rounded-full text-white cursor-pointer"
          style={{ backgroundColor: "rgba(5,6,8,0.6)", border: "1px solid rgba(255,255,255,0.2)", backdropFilter: "blur(8px)", boxShadow: "0 8px 24px rgba(0,0,0,0.4)" }}
        >
          <ChevronRightIcon />
        </button>

        {/* Dots: 24px hit areas around 8px marks */}
        <div style={{ display: "flex", alignItems: "center", justifyContent: "center", gap: "4px", zIndex: 30 }}>
          {items.map((item, idx) => (
            <button
              key={idx}
              type="button"
              onClick={() => goToSlide(idx)}
              aria-label={`Show ${item.titleLine1}`}
              aria-current={idx === currentIndex ? "true" : undefined}
              style={{ width: idx === currentIndex ? "44px" : "24px", height: "24px", background: "none", border: "none", cursor: "pointer", padding: 0, display: "flex", alignItems: "center", justifyContent: "center" }}
            >
              <span
                aria-hidden="true"
                style={{
                  display: "block",
                  height: "8px",
                  width: idx === currentIndex ? "28px" : "8px",
                  borderRadius: "9999px",
                  backgroundColor: idx === currentIndex ? ACCENT : "rgba(243,245,248,0.28)",
                  boxShadow: idx === currentIndex ? "0 0 10px rgba(58,143,224,0.7)" : "none",
                  transition: reduceMotion ? "none" : "all 300ms ease",
                }}
              />
            </button>
          ))}
        </div>
      </div>
    </section>
  );
}

export const Component = CoverFlowCarousel;
export default CoverFlowCarousel;
