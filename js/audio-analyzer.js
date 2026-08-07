class LMNAudioAnalyzer {
  constructor() {
    this.fftSize = 4096;
    this.maxSpectralFrames = 48;
  }

  async analyze(file, onProgress = () => {}) {
    if (!file) throw new Error('Aucun fichier audio sélectionné.');
    const supported = ['audio/mpeg', 'audio/mp3', 'audio/wav', 'audio/x-wav', 'audio/wave'];
    const ext = (file.name.split('.').pop() || '').toLowerCase();
    if (!supported.includes(file.type) && !['mp3', 'wav'].includes(ext)) {
      throw new Error('Format non supporté. Utilise un fichier MP3 ou WAV.');
    }

    onProgress(5, 'Lecture du fichier…');
    const bytes = await file.arrayBuffer();

    onProgress(12, 'Décodage PCM…');
    const AudioCtx = window.AudioContext || window.webkitAudioContext;
    if (!AudioCtx) throw new Error('Web Audio API non disponible dans ce navigateur.');
    const ctx = new AudioCtx();
    let buffer;
    try {
      buffer = await ctx.decodeAudioData(bytes.slice(0));
    } finally {
      await ctx.close();
    }

    onProgress(22, 'Analyse amplitude / dynamique…');
    const channels = Array.from({ length: buffer.numberOfChannels }, (_, i) => buffer.getChannelData(i));
    const mono = this.toMono(channels);
    const amplitude = this.analyzeAmplitude(mono);
    const stereo = this.analyzeStereo(channels);

    onProgress(38, 'Détection du tempo…');
    const rhythm = this.analyzeTempo(mono, buffer.sampleRate);

    onProgress(52, 'Analyse spectrale FFT…');
    const spectral = this.analyzeSpectral(mono, buffer.sampleRate, pct => {
      onProgress(52 + pct * 0.24, 'Analyse spectrale FFT…');
    });

    onProgress(78, 'Détection tonalité / chroma…');
    const key = this.detectKey(spectral.chroma);

    onProgress(86, 'Construction de la timeline…');
    const timeline = this.analyzeTimeline(mono, 12);
    const waveformPeaks = this.waveformPeaks(mono, 240);
    const dna = this.deriveDNA(amplitude, stereo, rhythm, spectral, key);
    const descriptors = this.deriveDescriptors(dna, rhythm, key, spectral);
    const diagnostics = this.buildDiagnostics(amplitude, stereo, rhythm, spectral, key);

    onProgress(96, 'Assemblage du rapport…');
    const duration = buffer.duration;
    const confidenceScore = Math.round(
      (rhythm.confidence * 0.35 + key.confidence * 0.35 + spectral.signalConfidence * 0.30) * 1000
    ) / 10;

    const result = {
      source: 'local-browser-analysis',
      file: {
        name: file.name,
        type: file.type || (ext === 'wav' ? 'audio/wav' : 'audio/mpeg'),
        format: ext.toUpperCase(),
        sizeBytes: file.size,
        sizeMB: +(file.size / 1048576).toFixed(2),
        durationSeconds: +duration.toFixed(3),
        duration: this.formatDuration(duration),
        sampleRate: buffer.sampleRate,
        channels: buffer.numberOfChannels
      },
      system: {
        version: 'v1.0-BROWSER-DSP',
        engine: 'LMNotebook Local Audio DSP',
        confidenceScore,
        timestamp: new Date().toISOString(),
        limitations: [
          'Le BPM et la tonalité sont des estimations DSP avec score de confiance.',
          'Les descripteurs de style sont heuristiques, pas une classification de genre par modèle ML.',
          'LUFS BS.1770, stems, transcription et classification neurale seront ajoutés côté backend.'
        ]
      },
      acoustics: {
        tempo: `${rhythm.bpm} BPM`,
        tempoConfidence: `${Math.round(rhythm.confidence * 100)}%`,
        key: `${key.tonic} ${key.mode}`,
        camelot: key.camelot,
        keyConfidence: `${Math.round(key.confidence * 100)}%`,
        rms: `${amplitude.rmsDb.toFixed(2)} dBFS`,
        peak: `${amplitude.peakDb.toFixed(2)} dBFS`,
        crestFactor: `${amplitude.crestDb.toFixed(2)} dB`,
        clipping: `${amplitude.clippingPercent.toFixed(4)}%`,
        dcOffset: amplitude.dcOffset.toFixed(6),
        zeroCrossingRate: amplitude.zeroCrossingRate.toFixed(4),
        spectralCentroid: `${Math.round(spectral.centroid)} Hz`,
        spectralRolloff: `${Math.round(spectral.rolloff)} Hz`,
        spectralFlatness: spectral.flatness.toFixed(4),
        spectralFlux: spectral.flux.toFixed(4),
        stereoWidth: `${Math.round(stereo.width * 100)}%`,
        stereoCorrelation: stereo.correlation.toFixed(3),
        stereoBalance: `${stereo.balance >= 0 ? '+' : ''}${(stereo.balance * 100).toFixed(1)}% R`,
        sampleRate: `${buffer.sampleRate} Hz`,
        channels: String(buffer.numberOfChannels),
        duration: this.formatDuration(duration)
      },
      dna,
      genres: descriptors,
      spectralBands: spectral.bands,
      emotionalTimeline: timeline,
      waveformPeaks,
      spectrogram: spectral.spectrogram,
      strengths: diagnostics.strengths,
      weaknesses: diagnostics.weaknesses,
      aiReport: diagnostics.report,
      raw: {
        rhythm,
        key,
        amplitude,
        stereo,
        spectral: {
          centroid: spectral.centroid,
          rolloff: spectral.rolloff,
          flatness: spectral.flatness,
          flux: spectral.flux,
          chroma: spectral.chroma
        }
      }
    };

    onProgress(100, 'Analyse terminée');
    return result;
  }

  toMono(channels) {
    if (channels.length === 1) return channels[0].slice();
    const length = channels[0].length;
    const mono = new Float32Array(length);
    for (let c = 0; c < channels.length; c++) {
      const ch = channels[c];
      for (let i = 0; i < length; i++) mono[i] += ch[i] / channels.length;
    }
    return mono;
  }

  analyzeAmplitude(samples) {
    let sumSq = 0;
    let peak = 0;
    let dc = 0;
    let clips = 0;
    let crossings = 0;
    let prev = samples[0] || 0;

    for (let i = 0; i < samples.length; i++) {
      const s = samples[i];
      const a = Math.abs(s);
      sumSq += s * s;
      dc += s;
      if (a > peak) peak = a;
      if (a >= 0.999) clips++;
      if ((s >= 0 && prev < 0) || (s < 0 && prev >= 0)) crossings++;
      prev = s;
    }

    const rms = Math.sqrt(sumSq / Math.max(1, samples.length));
    const rmsDb = this.toDb(rms);
    const peakDb = this.toDb(peak);
    return {
      rms,
      rmsDb,
      peak,
      peakDb,
      crestDb: peakDb - rmsDb,
      clippingPercent: clips / Math.max(1, samples.length) * 100,
      dcOffset: dc / Math.max(1, samples.length),
      zeroCrossingRate: crossings / Math.max(1, samples.length - 1)
    };
  }

  analyzeStereo(channels) {
    if (channels.length < 2) return { width: 0, correlation: 1, balance: 0, midRms: 0, sideRms: 0 };
    const l = channels[0];
    const r = channels[1];
    const step = Math.max(1, Math.floor(l.length / 250000));
    let ll = 0, rr = 0, lr = 0, midSq = 0, sideSq = 0, n = 0;

    for (let i = 0; i < l.length; i += step) {
      const lv = l[i], rv = r[i];
      ll += lv * lv;
      rr += rv * rv;
      lr += lv * rv;
      const mid = (lv + rv) * 0.5;
      const side = (lv - rv) * 0.5;
      midSq += mid * mid;
      sideSq += side * side;
      n++;
    }

    const rmsL = Math.sqrt(ll / n);
    const rmsR = Math.sqrt(rr / n);
    const midRms = Math.sqrt(midSq / n);
    const sideRms = Math.sqrt(sideSq / n);
    const correlation = lr / Math.sqrt(Math.max(1e-12, ll * rr));
    const balance = (rmsR - rmsL) / Math.max(1e-12, rmsR + rmsL);
    const width = this.clamp(sideRms / Math.max(1e-9, midRms), 0, 2) / 2;
    return { width, correlation, balance, midRms, sideRms };
  }

  analyzeTempo(samples, sampleRate) {
    const hop = 1024;
    const frame = 2048;
    const frameCount = Math.floor((samples.length - frame) / hop);
    if (frameCount < 32) return { bpm: 0, confidence: 0, beatPeriodFrames: 0 };

    const env = new Float32Array(frameCount);
    let prevEnergy = 0;
    for (let f = 0; f < frameCount; f++) {
      const start = f * hop;
      let sum = 0;
      for (let i = 0; i < frame; i += 4) {
        const s = samples[start + i] || 0;
        sum += s * s;
      }
      const energy = Math.sqrt(sum / (frame / 4));
      env[f] = Math.max(0, energy - prevEnergy);
      prevEnergy = energy;
    }

    const mean = env.reduce((a, b) => a + b, 0) / env.length;
    for (let i = 0; i < env.length; i++) env[i] = Math.max(0, env[i] - mean * 0.5);

    const frameRate = sampleRate / hop;
    const minBpm = 60;
    const maxBpm = 200;
    const minLag = Math.max(1, Math.floor(frameRate * 60 / maxBpm));
    const maxLag = Math.min(env.length - 2, Math.ceil(frameRate * 60 / minBpm));
    let bestLag = minLag;
    let best = -Infinity;
    let sumScores = 0;
    let scoreCount = 0;

    for (let lag = minLag; lag <= maxLag; lag++) {
      let score = 0;
      let normA = 0;
      let normB = 0;
      for (let i = lag; i < env.length; i++) {
        const a = env[i];
        const b = env[i - lag];
        score += a * b;
        normA += a * a;
        normB += b * b;
      }
      score /= Math.sqrt(Math.max(1e-12, normA * normB));
      const bpm = 60 * frameRate / lag;
      const preference = 0.88 + 0.12 * Math.exp(-Math.pow((bpm - 120) / 55, 2));
      score *= preference;
      sumScores += score;
      scoreCount++;
      if (score > best) {
        best = score;
        bestLag = lag;
      }
    }

    let bpm = 60 * frameRate / bestLag;
    while (bpm < 70) bpm *= 2;
    while (bpm > 190) bpm /= 2;
    const avg = sumScores / Math.max(1, scoreCount);
    const confidence = this.clamp((best - avg) * 2.8 + best * 0.45, 0, 0.99);
    return { bpm: Math.round(bpm * 10) / 10, confidence, beatPeriodFrames: bestLag };
  }

  analyzeSpectral(samples, sampleRate, onProgress = () => {}) {
    const N = this.fftSize;
    const usable = Math.max(1, samples.length - N);
    const frameCount = Math.min(this.maxSpectralFrames, Math.max(8, Math.floor(samples.length / N)));
    const chroma = new Float64Array(12);
    const spectrogram = [];
    let centroidTotal = 0;
    let rolloffTotal = 0;
    let flatnessTotal = 0;
    let fluxTotal = 0;
    let prevNorm = null;
    let validFrames = 0;
    const bandTotals = { sub: 0, bass: 0, lowMid: 0, mid: 0, presence: 0, air: 0 };

    for (let f = 0; f < frameCount; f++) {
      const pos = Math.floor((f / Math.max(1, frameCount - 1)) * usable);
      const re = new Float64Array(N);
      const im = new Float64Array(N);
      for (let i = 0; i < N; i++) {
        const win = 0.5 - 0.5 * Math.cos(2 * Math.PI * i / (N - 1));
        re[i] = (samples[pos + i] || 0) * win;
      }
      this.fft(re, im);

      const bins = N / 2;
      const mags = new Float64Array(bins);
      let magSum = 0;
      let weighted = 0;
      let energySum = 0;
      let logSum = 0;
      for (let k = 1; k < bins; k++) {
        const mag = Math.hypot(re[k], im[k]) + 1e-12;
        mags[k] = mag;
        const freq = k * sampleRate / N;
        magSum += mag;
        weighted += freq * mag;
        const e = mag * mag;
        energySum += e;
        logSum += Math.log(mag);

        if (freq >= 40 && freq <= 5000) {
          const midi = Math.round(69 + 12 * Math.log2(freq / 440));
          const pc = ((midi % 12) + 12) % 12;
          chroma[pc] += e;
        }

        if (freq < 60) bandTotals.sub += e;
        else if (freq < 250) bandTotals.bass += e;
        else if (freq < 500) bandTotals.lowMid += e;
        else if (freq < 2000) bandTotals.mid += e;
        else if (freq < 6000) bandTotals.presence += e;
        else if (freq < 16000) bandTotals.air += e;
      }

      if (magSum <= 1e-10) continue;
      validFrames++;
      centroidTotal += weighted / magSum;

      let cumulative = 0;
      const target = energySum * 0.85;
      let rolloff = 0;
      for (let k = 1; k < bins; k++) {
        cumulative += mags[k] * mags[k];
        if (cumulative >= target) {
          rolloff = k * sampleRate / N;
          break;
        }
      }
      rolloffTotal += rolloff;
      const arithmeticMean = magSum / (bins - 1);
      flatnessTotal += Math.exp(logSum / (bins - 1)) / Math.max(1e-12, arithmeticMean);

      const norm = new Float64Array(bins);
      for (let k = 1; k < bins; k++) norm[k] = mags[k] / magSum;
      if (prevNorm) {
        let flux = 0;
        for (let k = 1; k < bins; k++) {
          const d = norm[k] - prevNorm[k];
          if (d > 0) flux += d * d;
        }
        fluxTotal += Math.sqrt(flux);
      }
      prevNorm = norm;

      const col = [];
      const visualBands = 32;
      const minFreq = 30;
      const maxFreq = Math.min(16000, sampleRate / 2);
      for (let b = 0; b < visualBands; b++) {
        const f1 = minFreq * Math.pow(maxFreq / minFreq, b / visualBands);
        const f2 = minFreq * Math.pow(maxFreq / minFreq, (b + 1) / visualBands);
        const k1 = Math.max(1, Math.floor(f1 * N / sampleRate));
        const k2 = Math.min(bins - 1, Math.ceil(f2 * N / sampleRate));
        let e = 0;
        for (let k = k1; k <= k2; k++) e += mags[k] * mags[k];
        col.push(Math.log10(1 + e));
      }
      spectrogram.push(col);
      onProgress((f + 1) / frameCount);
    }

    const chromaSum = chroma.reduce((a, b) => a + b, 0) || 1;
    for (let i = 0; i < chroma.length; i++) chroma[i] /= chromaSum;

    let maxSpec = 0;
    spectrogram.forEach(col => col.forEach(v => { if (v > maxSpec) maxSpec = v; }));
    if (maxSpec > 0) spectrogram.forEach(col => { for (let i = 0; i < col.length; i++) col[i] /= maxSpec; });

    const bandSum = Object.values(bandTotals).reduce((a, b) => a + b, 0) || 1;
    const bands = Object.entries(bandTotals).map(([name, value]) => ({ name, value: +(value / bandSum * 100).toFixed(2) }));
    const vf = Math.max(1, validFrames);
    const flatness = flatnessTotal / vf;
    const signalConfidence = this.clamp(1 - flatness * 0.75, 0.35, 0.98);

    return {
      centroid: centroidTotal / vf,
      rolloff: rolloffTotal / vf,
      flatness,
      flux: fluxTotal / Math.max(1, vf - 1),
      chroma: Array.from(chroma),
      spectrogram,
      bands,
      signalConfidence
    };
  }

  detectKey(chroma) {
    const major = [6.35, 2.23, 3.48, 2.33, 4.38, 4.09, 2.52, 5.19, 2.39, 3.66, 2.29, 2.88];
    const minor = [6.33, 2.68, 3.52, 5.38, 2.60, 3.53, 2.54, 4.75, 3.98, 2.69, 3.34, 3.17];
    const names = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B'];
    const results = [];

    for (let tonic = 0; tonic < 12; tonic++) {
      results.push({ tonic, mode: 'Major', score: this.profileCorrelation(chroma, major, tonic) });
      results.push({ tonic, mode: 'Minor', score: this.profileCorrelation(chroma, minor, tonic) });
    }
    results.sort((a, b) => b.score - a.score);
    const best = results[0];
    const second = results[1];
    const confidence = this.clamp(0.45 + (best.score - second.score) * 0.9 + Math.max(0, best.score) * 0.25, 0.2, 0.98);
    return {
      tonic: names[best.tonic],
      mode: best.mode,
      confidence,
      score: best.score,
      camelot: this.camelot(names[best.tonic], best.mode)
    };
  }

  profileCorrelation(chroma, profile, tonic) {
    const rotated = profile.map((_, i) => profile[(i - tonic + 12) % 12]);
    return this.correlation(chroma, rotated);
  }

  camelot(tonic, mode) {
    const major = { C: '8B', G: '9B', D: '10B', A: '11B', E: '12B', B: '1B', 'F#': '2B', 'C#': '3B', 'G#': '4B', 'D#': '5B', 'A#': '6B', F: '7B' };
    const minor = { A: '8A', E: '9A', B: '10A', 'F#': '11A', 'C#': '12A', 'G#': '1A', 'D#': '2A', 'A#': '3A', F: '4A', C: '5A', G: '6A', D: '7A' };
    return mode === 'Major' ? major[tonic] : minor[tonic];
  }

  analyzeTimeline(samples, segments) {
    const chunk = Math.max(1, Math.floor(samples.length / segments));
    const values = [];
    for (let s = 0; s < segments; s++) {
      const start = s * chunk;
      const end = s === segments - 1 ? samples.length : Math.min(samples.length, start + chunk);
      let sum = 0;
      for (let i = start; i < end; i += 8) sum += samples[i] * samples[i];
      const n = Math.max(1, Math.ceil((end - start) / 8));
      values.push(Math.sqrt(sum / n));
    }
    const min = Math.min(...values);
    const max = Math.max(...values);
    return values.map((v, i) => {
      const intensity = max === min ? 50 : 20 + 80 * (v - min) / (max - min);
      return {
        phase: `${Math.round(i / segments * 100)}%`,
        emotion: 'Energy',
        intensity: Math.round(intensity)
      };
    });
  }

  waveformPeaks(samples, points) {
    const block = Math.max(1, Math.floor(samples.length / points));
    const peaks = [];
    for (let p = 0; p < points; p++) {
      const start = p * block;
      const end = Math.min(samples.length, start + block);
      let peak = 0;
      for (let i = start; i < end; i++) peak = Math.max(peak, Math.abs(samples[i]));
      peaks.push(peak);
    }
    return peaks;
  }

  deriveDNA(amplitude, stereo, rhythm, spectral, key) {
    const energy = this.clamp((amplitude.rmsDb + 32) / 25, 0, 1);
    const tempoFit = Math.exp(-Math.pow((rhythm.bpm - 122) / 55, 2));
    const rhythmScore = this.clamp(rhythm.confidence * 0.8 + tempoFit * 0.2, 0, 1);
    const brightness = this.clamp(spectral.centroid / 6500, 0, 1);
    const dynamics = this.clamp((amplitude.crestDb - 3) / 13, 0, 1);
    const stereoWidth = this.clamp(stereo.width, 0, 1);
    const tonality = this.clamp(key.confidence, 0, 1);
    return { energy, rhythm: rhythmScore, brightness, dynamics, stereoWidth, tonality };
  }

  deriveDescriptors(dna, rhythm, key, spectral) {
    const list = [];
    const add = (name, weight) => list.push({ name, weight: Math.round(this.clamp(weight, 0, 1) * 100) });
    add(dna.energy > 0.68 ? 'High Energy' : dna.energy < 0.35 ? 'Low Energy' : 'Balanced Energy', Math.abs(dna.energy - 0.5) * 1.4 + 0.35);
    add(dna.brightness > 0.55 ? 'Bright Timbre' : 'Warm / Dark Timbre', Math.abs(dna.brightness - 0.5) * 1.5 + 0.3);
    add(dna.dynamics > 0.58 ? 'Dynamic' : 'Dense / Compressed', Math.abs(dna.dynamics - 0.5) * 1.5 + 0.3);
    add(dna.stereoWidth > 0.5 ? 'Wide Stereo' : 'Focused Stereo', Math.abs(dna.stereoWidth - 0.5) * 1.4 + 0.35);
    add(rhythm.bpm >= 115 && rhythm.bpm <= 150 ? 'Club Tempo Range' : 'Non-club Tempo Range', rhythm.confidence);
    add(`${key.mode} Tonality`, key.confidence);
    if (spectral.flatness > 0.3) add('Noisy / Textured Spectrum', spectral.flatness);
    else add('Tonal Spectrum', 1 - spectral.flatness);
    return list.sort((a, b) => b.weight - a.weight).slice(0, 7);
  }

  buildDiagnostics(amplitude, stereo, rhythm, spectral, key) {
    const strengths = [];
    const weaknesses = [];
    if (amplitude.clippingPercent < 0.001) strengths.push('Aucun clipping numérique significatif détecté.');
    else weaknesses.push(`Clipping détecté sur ${amplitude.clippingPercent.toFixed(4)}% des échantillons.`);
    if (Math.abs(stereo.balance) < 0.05) strengths.push('Balance gauche/droite très bien centrée.');
    else weaknesses.push('Déséquilibre stéréo mesurable entre les canaux gauche et droit.');
    if (stereo.correlation > 0.15) strengths.push('Corrélation stéréo compatible avec une bonne stabilité mono.');
    else weaknesses.push('Corrélation stéréo faible ou négative : vérifier la compatibilité mono / phase.');
    if (amplitude.crestDb >= 7) strengths.push('Réserve dynamique perceptible entre RMS et crête.');
    else weaknesses.push('Crest factor faible : signal dense ou fortement limité.');
    if (rhythm.confidence > 0.55) strengths.push(`Tempo détecté avec une confiance correcte (${Math.round(rhythm.confidence * 100)}%).`);
    else weaknesses.push('Tempo ambigu : groove libre, syncopes fortes ou détection à confirmer manuellement.');
    if (key.confidence > 0.55) strengths.push(`Centre tonal relativement clair (${key.tonic} ${key.mode}).`);
    else weaknesses.push('Tonalité ambiguë : modulation, chromatisme ou contenu percussif dominant possible.');
    if (!weaknesses.length) weaknesses.push('Aucune anomalie DSP évidente détectée par ce scan navigateur.');

    const report = {
      summary: `Analyse locale réelle du signal : ${rhythm.bpm} BPM estimés, tonalité ${key.tonic} ${key.mode} (${this.camelot(key.tonic, key.mode)}), RMS ${amplitude.rmsDb.toFixed(1)} dBFS et crête ${amplitude.peakDb.toFixed(1)} dBFS.`,
      technicalDiagnosis: `Le centroïde spectral moyen est d’environ ${Math.round(spectral.centroid)} Hz, avec un roll-off 85% à ${Math.round(spectral.rolloff)} Hz. La largeur stéréo calculée est de ${Math.round(stereo.width * 100)}% et la corrélation L/R de ${stereo.correlation.toFixed(2)}.`,
      strategicRecommendation: 'Ce premier moteur est volontairement DSP-first : il mesure ce qui est réellement extractible dans le navigateur. Pour des genres, instruments, stems, paroles, structure couplet/refrain et embeddings fiables, branche un backend Python avec modèles spécialisés.'
    };
    return { strengths, weaknesses, report };
  }

  fft(re, im) {
    const n = re.length;
    for (let i = 1, j = 0; i < n; i++) {
      let bit = n >> 1;
      for (; j & bit; bit >>= 1) j ^= bit;
      j ^= bit;
      if (i < j) {
        [re[i], re[j]] = [re[j], re[i]];
        [im[i], im[j]] = [im[j], im[i]];
      }
    }
    for (let len = 2; len <= n; len <<= 1) {
      const ang = -2 * Math.PI / len;
      const wLenCos = Math.cos(ang);
      const wLenSin = Math.sin(ang);
      for (let i = 0; i < n; i += len) {
        let wCos = 1, wSin = 0;
        for (let j = 0; j < len / 2; j++) {
          const uRe = re[i + j], uIm = im[i + j];
          const vRe0 = re[i + j + len / 2], vIm0 = im[i + j + len / 2];
          const vRe = vRe0 * wCos - vIm0 * wSin;
          const vIm = vRe0 * wSin + vIm0 * wCos;
          re[i + j] = uRe + vRe;
          im[i + j] = uIm + vIm;
          re[i + j + len / 2] = uRe - vRe;
          im[i + j + len / 2] = uIm - vIm;
          const nextCos = wCos * wLenCos - wSin * wLenSin;
          wSin = wCos * wLenSin + wSin * wLenCos;
          wCos = nextCos;
        }
      }
    }
  }

  correlation(a, b) {
    const n = Math.min(a.length, b.length);
    let ma = 0, mb = 0;
    for (let i = 0; i < n; i++) { ma += a[i]; mb += b[i]; }
    ma /= n; mb /= n;
    let num = 0, da = 0, db = 0;
    for (let i = 0; i < n; i++) {
      const xa = a[i] - ma;
      const xb = b[i] - mb;
      num += xa * xb;
      da += xa * xa;
      db += xb * xb;
    }
    return num / Math.sqrt(Math.max(1e-12, da * db));
  }

  formatDuration(seconds) {
    const s = Math.max(0, Math.round(seconds));
    const m = Math.floor(s / 60);
    return `${m}:${String(s % 60).padStart(2, '0')}`;
  }

  toDb(v) {
    return 20 * Math.log10(Math.max(1e-12, v));
  }

  clamp(v, min, max) {
    return Math.min(max, Math.max(min, v));
  }
}

window.LMNAudioAnalyzer = LMNAudioAnalyzer;
