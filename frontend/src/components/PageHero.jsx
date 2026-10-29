import React from 'react';

export function PageHero({ eyebrow, title, description, image, children }) {
  return (
    <section className="relative isolate overflow-hidden rounded-[28px] bg-slate-950 px-6 py-10 sm:px-10 sm:py-12 lg:px-12 lg:py-14 text-white shadow-xl">
      <img
        src={image}
        alt=""
        className="absolute inset-0 -z-20 h-full w-full object-cover object-center"
      />
      <div className="absolute inset-0 -z-10 bg-gradient-to-r from-slate-950/95 via-slate-950/75 to-slate-950/35" />
      <div className="max-w-2xl">
        {eyebrow && (
          <div className="mb-4 text-[11px] font-bold uppercase tracking-[0.18em] text-amber-300">
            {eyebrow}
          </div>
        )}
        <h1 className="font-serif text-4xl leading-tight sm:text-5xl lg:text-[56px]">{title}</h1>
        {description && <p className="mt-4 max-w-xl text-sm leading-7 text-slate-200 sm:text-base">{description}</p>}
        {children && <div className="mt-6 flex flex-wrap gap-3">{children}</div>}
      </div>
    </section>
  );
}
