import React from "react";
import {
	AbsoluteFill,
	Audio,
	Img,
	interpolate,
	spring,
	staticFile,
	useCurrentFrame,
	useVideoConfig,
} from "remotion";
import {parseSrt} from "@remotion/captions";

// `@remotion/captions`'ın `createTikTokStyleCaptions`'ı, ardışık kelimeleri tek sayfada
// birleştirmek için metnin BAŞINDA BOŞLUK olmasını şart koşuyor (ASR-tarzı " kelime" parçaları
// için tasarlanmış); bizim SRT'deki kelimeler boşluksuz olduğundan hiç sayfa bölünmüyordu — tüm
// cümle tek ekranda kalıyordu. Bunun yerine basit, öngörülebilir kendi sayfalamamızı yapıyoruz:
// art arda gelen kelimeleri azami kelime sayısı ya da büyük bir sessizlik boşluğuna göre böl.
const sayfalaraBol = (captions, azamiKelime = 3, bosluklaBol = 500) => {
	const sayfalar = [];
	let mevcut = [];
	captions.forEach((altyazi, i) => {
		const onceki = captions[i - 1];
		const buyukBosluk = onceki && altyazi.startMs - onceki.endMs > bosluklaBol;
		if (mevcut.length && (mevcut.length >= azamiKelime || buyukBosluk)) {
			sayfalar.push(mevcut);
			mevcut = [];
		}
		mevcut.push(altyazi);
	});
	if (mevcut.length) sayfalar.push(mevcut);
	return sayfalar.map((kelimeler) => ({
		startMs: kelimeler[0].startMs,
		endMs: kelimeler[kelimeler.length - 1].endMs,
		kelimeler,
	}));
};

// Bu bileşen hiçbir sayı/cümle uydurmaz — fiyat/indirim yalnız props'tan (veri/YYYY-Www.json
// kaynaklı), altyazı yalnız edge-tts'in ürettiği SRT metninden gelir. bkz. ANAYASA §2.

const bicimFiyat = (deger, paraBirimi) => {
	if (deger === null || deger === undefined) return null;
	return `${Number(deger).toLocaleString("tr-TR")} ${paraBirimi || "TL"}`;
};

const FiyatEtiketi = ({fiyat, indirim, indirimOran, paraBirimi}) => {
	const frame = useCurrentFrame();
	const {fps} = useVideoConfig();
	if (indirimOran === null || indirimOran === undefined) return null;
	const giris = spring({frame: frame - Math.round(fps * 0.5), fps, config: {damping: 14}});
	return (
		<div
			style={{
				position: "absolute",
				top: 140,
				right: 40,
				background: "#1b3a2f",
				color: "white",
				borderRadius: 20,
				padding: "18px 26px",
				transform: `scale(${giris})`,
				opacity: giris,
				fontFamily: "sans-serif",
				textAlign: "center",
				boxShadow: "0 8px 24px rgba(0,0,0,0.35)",
			}}
		>
			<div style={{fontSize: 40, fontWeight: 800}}>%{indirimOran} İndirim</div>
			{indirim !== null && indirim !== undefined && (
				<div style={{fontSize: 28, marginTop: 6}}>
					{fiyat !== null && fiyat !== undefined && (
						<span style={{textDecoration: "line-through", opacity: 0.6, marginRight: 10}}>
							{bicimFiyat(fiyat, paraBirimi)}
						</span>
					)}
					<span style={{fontWeight: 700}}>{bicimFiyat(indirim, paraBirimi)}</span>
				</div>
			)}
		</div>
	);
};

const Altyazi = ({altyaziSrtMetni}) => {
	const frame = useCurrentFrame();
	const {fps} = useVideoConfig();
	const simdiMs = (frame / fps) * 1000;
	if (!altyaziSrtMetni) return null;
	const {captions} = parseSrt({input: altyaziSrtMetni});
	if (!captions.length) return null;
	const sayfalar = sayfalaraBol(captions);
	const sayfa = sayfalar.find((s) => simdiMs >= s.startMs && simdiMs <= s.endMs);
	if (!sayfa) return null;
	return (
		<div
			style={{
				position: "absolute",
				bottom: 160,
				left: 60,
				right: 60,
				display: "flex",
				flexWrap: "wrap",
				justifyContent: "center",
				textAlign: "center",
				fontFamily: "sans-serif",
				fontSize: 52,
				fontWeight: 800,
				color: "white",
				textShadow: "0 2px 10px rgba(0,0,0,0.8)",
			}}
		>
			{sayfa.kelimeler.map((kelime, i) => {
				const aktif = simdiMs >= kelime.startMs && simdiMs < kelime.endMs;
				return (
					<span key={i} style={{color: aktif ? "#ffd23f" : "white", marginRight: 12}}>
						{kelime.text}
					</span>
				);
			})}
		</div>
	);
};

export const UrunVideosu = ({
	gorselYolu,
	sesYolu,
	altyaziSrtMetni,
	fiyat,
	indirim,
	indirimOran,
	paraBirimi,
}) => {
	const frame = useCurrentFrame();
	const {durationInFrames} = useVideoConfig();
	const olcek = interpolate(frame, [0, durationInFrames], [1, 1.08]);
	return (
		<AbsoluteFill style={{backgroundColor: "black"}}>
			{gorselYolu && (
				<Img
					src={staticFile(gorselYolu)}
					style={{
						width: "100%",
						height: "100%",
						objectFit: "cover",
						transform: `scale(${olcek})`,
					}}
				/>
			)}
			<FiyatEtiketi fiyat={fiyat} indirim={indirim} indirimOran={indirimOran} paraBirimi={paraBirimi} />
			<Altyazi altyaziSrtMetni={altyaziSrtMetni} />
			{sesYolu && <Audio src={staticFile(sesYolu)} />}
		</AbsoluteFill>
	);
};
