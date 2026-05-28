% generate_fixtures.m
%
% Run the original MATLAB Contourlet Toolbox under Octave to produce
% reference outputs for every public function. The pytest parity suite
% loads these .mat files and compares against the Python implementation
% with np.testing.assert_allclose.
%
% Usage:
%   octave --no-gui --eval "addpath('<TOOLBOX>'); \
%      generate_fixtures('<OUT>')"
%
% Args:
%   out_dir       -- directory to write .mat files into (default:
%                    tests/fixtures)
%
% Conventions for saved files:
%   * scalars and matrices are saved directly under their MATLAB names
%   * cell vectors are unpacked into numbered fields, e.g. y{1}, y{2}, ...
%     are saved as y_1, y_2, ... so scipy.io.loadmat can read them.
%   * pdfbdec output saves the lowpass as `lowpass` and each layer's
%     directional subbands flattened as `layer_<i>_dir_<k>`.

function generate_fixtures(out_dir)
    if nargin < 1
        out_dir = 'tests/fixtures';
    end
    if exist(out_dir, 'dir') ~= 7
        mkdir(out_dir);
    end

    % Guard: make sure the MATLAB Contourlet Toolbox is on addpath. If not,
    % fail fast with an actionable message so the user doesn't see a
    % cryptic "undefined function pfilters" error after a partial run.
    if exist('pfilters', 'file') ~= 2
        error([ ...
            'Contourlet Toolbox not on path. Invoke as:\n' ...
            '  octave --no-gui --eval "addpath(''<TOOLBOX_PATH>''); ' ...
            'addpath(''tests/octave''); generate_fixtures(''<OUT>'')"\n' ...
            'where <TOOLBOX_PATH> contains pfilters.m, dfilters.m, etc.']);
    end

    % Deterministic inputs
    X16 = reshape(1:256, 16, 16) / 256;
    X32 = reshape(1:1024, 32, 32) / 1024;
    rand('state', 42);
    R32 = randn(32, 32);

    fprintf('Writing fixtures to %s\n', out_dir);

    %% ---- Filter generators ----------------------------------------------
    % maxflat falls through to Wavelet Toolbox's wfilters in MATLAB; not in
    % Octave. Skip it; Python implements it directly.
    pf_names = {'9-7', '5-3', 'Burt', 'pkva'};
    for i = 1:length(pf_names)
        n = pf_names{i};
        [h, g] = pfilters(n);
        save('-v6', fullfile(out_dir, ['pfilters_' slugify(n) '.mat']), ...
             'h', 'g');
    end

    df_names = {'haar', '9-7', 'cd', '5-3', 'pkva', 'pkva6', 'pkva8', 'pkva12'};
    for i = 1:length(df_names)
        n = df_names{i};
        for tp = {'d', 'r'}
            t = tp{1};
            [h0, h1] = dfilters(n, t);
            save('-v6', ...
                 fullfile(out_dir, ['dfilters_' slugify(n) '_' t '.mat']), ...
                 'h0', 'h1');
        end
    end

    ld_names = {'pkva', 'pkva6', 'pkva8', 'pkva12'};
    for i = 1:length(ld_names)
        n = ld_names{i};
        f = ldfilter(n);
        save('-v6', fullfile(out_dir, ['ldfilter_' n '.mat']), 'f');
    end

    beta = ldfilter('pkva');
    [h0, h1] = ld2quin(beta);
    save('-v6', fullfile(out_dir, 'ld2quin_pkva.mat'), 'beta', 'h0', 'h1');

    [h, ~] = pfilters('9-7');
    t = [0, 1, 0; 1, 0, 1; 0, 1, 0] / 4;
    h2d = mctrans(h, t);
    save('-v6', fullfile(out_dir, 'mctrans_9_7.mat'), 'h', 't', 'h2d');

    M = X16;
    y = modulate2(M, 'r');
    save('-v6', fullfile(out_dir, 'modulate2_r.mat'), 'M', 'y');
    y = modulate2(M, 'c');
    save('-v6', fullfile(out_dir, 'modulate2_c.mat'), 'M', 'y');
    y = modulate2(M, 'b');
    save('-v6', fullfile(out_dir, 'modulate2_b.mat'), 'M', 'y');

    y = reverse2(M);
    save('-v6', fullfile(out_dir, 'reverse2.mat'), 'M', 'y');

    [h0, h1] = dfilters('cd', 'd');
    [f0, f1] = ffilters(h0, h1);
    f0_1 = f0{1}; f0_2 = f0{2}; f0_3 = f0{3}; f0_4 = f0{4};
    f1_1 = f1{1}; f1_2 = f1{2}; f1_3 = f1{3}; f1_4 = f1{4};
    save('-v6', fullfile(out_dir, 'ffilters_cd_d.mat'), ...
         'h0', 'h1', 'f0_1', 'f0_2', 'f0_3', 'f0_4', ...
         'f1_1', 'f1_2', 'f1_3', 'f1_4');

    %% ---- Sampling primitives --------------------------------------------
    % resampc periodic mode
    for rt = [1, 2]
        for sh = [1, 2]
            x = R32;
            rtype = rt;
            shift = sh;
            y = resampc(R32, rt, sh, 'per');
            save('-v6', ...
                 fullfile(out_dir, sprintf('resampc_t%d_s%d.mat', rt, sh)), ...
                 'x', 'rtype', 'shift', 'y');
        end
    end

    % resamp 1..4
    for rt = 1:4
        x = R32;
        rtype = rt;
        y = resamp(R32, rt);
        save('-v6', fullfile(out_dir, sprintf('resamp_t%d.mat', rt)), ...
             'x', 'rtype', 'y');
    end

    % resampz 1..4
    for rt = 1:4
        x = R32;
        rtype = rt;
        y = resampz(R32, rt);
        save('-v6', fullfile(out_dir, sprintf('resampz_t%d.mat', rt)), ...
             'x', 'rtype', 'y');
    end

    % qupz
    for tp = [1, 2]
        x = X16;
        qtype = tp;
        y = qupz(X16, tp);
        save('-v6', fullfile(out_dir, sprintf('qupz_t%d.mat', tp)), ...
             'x', 'qtype', 'y');
    end

    % dup
    x = X16;
    step = [2, 2];
    phase = [0, 0];
    y = dup(X16, [2, 2], [0, 0]);
    save('-v6', fullfile(out_dir, 'dup_2x2_zero.mat'), 'x', 'step', 'phase', 'y');
    phase = 'm';
    y = dup(X16, [2, 2], 'm');
    save('-v6', fullfile(out_dir, 'dup_minimum.mat'), 'x', 'step', 'phase', 'y');

    % qdown / qup
    qtypes = {'1r', '1c', '2r', '2c'};
    for i = 1:length(qtypes)
        qt = qtypes{i};
        x = R32;
        qtype = qt;
        y = qdown(R32, qt);
        save('-v6', fullfile(out_dir, ['qdown_' qt '.mat']), ...
             'x', 'qtype', 'y');
        rec = qup(y, qt);
        save('-v6', fullfile(out_dir, ['qup_' qt '.mat']), ...
             'y', 'qtype', 'rec');
    end

    % pdown / pup
    for pt = 1:4
        x = R32;
        ptype = pt;
        y = pdown(R32, pt);
        save('-v6', fullfile(out_dir, sprintf('pdown_t%d.mat', pt)), ...
             'x', 'ptype', 'y');
        rec = pup(y, pt);
        save('-v6', fullfile(out_dir, sprintf('pup_t%d.mat', pt)), ...
             'y', 'ptype', 'rec');
    end

    %% ---- Polyphase decomposition / reconstruction -----------------------
    for i = 1:length(qtypes)
        qt = qtypes{i};
        x = R32;
        qtype = qt;
        [p0, p1] = qpdec(R32, qt);
        save('-v6', fullfile(out_dir, ['qpdec_' qt '.mat']), ...
             'x', 'qtype', 'p0', 'p1');
        x_rec = qprec(p0, p1, qt);
        save('-v6', fullfile(out_dir, ['qprec_' qt '.mat']), ...
             'p0', 'p1', 'qtype', 'x_rec');
    end
    for pt = 1:4
        x = R32;
        ptype = pt;
        [p0, p1] = ppdec(R32, pt);
        save('-v6', fullfile(out_dir, sprintf('ppdec_t%d.mat', pt)), ...
             'x', 'ptype', 'p0', 'p1');
        x_rec = pprec(p0, p1, pt);
        save('-v6', fullfile(out_dir, sprintf('pprec_t%d.mat', pt)), ...
             'p0', 'p1', 'ptype', 'x_rec');
    end

    %% ---- Extension / filtering primitives -------------------------------
    x = R32; ru = 2; rd = 3; cl = 1; cr = 4; extmod = 'per';
    y = extend2(R32, 2, 3, 1, 4, 'per');
    save('-v6', fullfile(out_dir, 'extend2_per.mat'), ...
         'x', 'ru', 'rd', 'cl', 'cr', 'extmod', 'y');

    x = R32; ru = 1; rd = 1; cl = 0; cr = 0; extmod = 'qper_row';
    y = extend2(R32, 1, 1, 0, 0, 'qper_row');
    save('-v6', fullfile(out_dir, 'extend2_qper_row.mat'), ...
         'x', 'ru', 'rd', 'cl', 'cr', 'extmod', 'y');

    x = R32; ru = 1; rd = 1; cl = 0; cr = 0; extmod = 'qper_col';
    y = extend2(R32, 1, 1, 0, 0, 'qper_col');
    save('-v6', fullfile(out_dir, 'extend2_qper_col.mat'), ...
         'x', 'ru', 'rd', 'cl', 'cr', 'extmod', 'y');

    [h, g] = pfilters('9-7');
    x = R32; f1 = h; f2 = h; extmod = 'per';
    y = sefilter2(R32, h, h, 'per');
    save('-v6', fullfile(out_dir, 'sefilter2_per.mat'), ...
         'x', 'f1', 'f2', 'extmod', 'y');

    f = h' * h;
    x = R32; extmod = 'per';
    y = efilter2(R32, h' * h, 'per');
    save('-v6', fullfile(out_dir, 'efilter2_per.mat'), 'x', 'f', 'extmod', 'y');

    %% ---- Laplacian pyramid / wavelet ------------------------------------
    pf = {'9-7', '5-3', 'Burt'};
    for i = 1:length(pf)
        n = pf{i};
        [h, g] = pfilters(n);
        [c, d] = lpdec(R32, h, g);
        rec = lprec(c, d, h, g);
        x = R32;
        save('-v6', fullfile(out_dir, ['lpdec_' slugify(n) '.mat']), ...
             'x', 'h', 'g', 'c', 'd');
        save('-v6', fullfile(out_dir, ['lprec_' slugify(n) '.mat']), ...
             'c', 'd', 'h', 'g', 'rec');
    end

    [h, g] = pfilters('9-7');
    [LL, LH, HL, HH] = wfb2dec(R32, h, g);
    rec = wfb2rec(LL, LH, HL, HH, h, g);
    x = R32;
    save('-v6', fullfile(out_dir, 'wfb2_9_7.mat'), ...
         'x', 'h', 'g', 'LL', 'LH', 'HL', 'HH', 'rec');

    %% ---- DFB ladder (pkva) and general (cd) -----------------------------
    for nlev = 1:3
        x = R32;
        fname = 'pkva';
        y = dfbdec_l(R32, 'pkva', nlev);
        rec = dfbrec_l(y, 'pkva');
        save_dfb(fullfile(out_dir, sprintf('dfb_l_pkva_n%d.mat', nlev)), ...
                 x, fname, nlev, y, rec);
    end

    df = {'cd', '9-7'};
    for i = 1:length(df)
        nm = df{i};
        for nlev = 1:3
            x = R32;
            fname = nm;
            y = dfbdec(R32, nm, nlev);
            rec = dfbrec(y, nm);
            save_dfb(fullfile(out_dir, ...
                              sprintf('dfb_%s_n%d.mat', slugify(nm), nlev)), ...
                     x, fname, nlev, y, rec);
        end
    end

    %% ---- PDFB end-to-end ------------------------------------------------
    nlevs = [2, 3];
    y = pdfbdec(R32, '9-7', 'pkva', nlevs);
    [c, s] = pdfb2vec(y);
    rec = pdfbrec(y, '9-7', 'pkva');
    save_pdfb(fullfile(out_dir, 'pdfb_9_7_pkva_2_3.mat'), ...
              R32, '9-7', 'pkva', nlevs, y, c, s, rec);

    %% ---- snr -------------------------------------------------------------
    in = R32;
    est = R32 + 0.05 * randn(32, 32);
    r = SNR(R32, est);
    save('-v6', fullfile(out_dir, 'snr_demo.mat'), 'in', 'est', 'r');

    fprintf('Done.\n');
end


function s = slugify(name)
    s = strrep(name, '/', '_');
    s = strrep(s, '-', '_');
end


function save_dfb(filename, x, fname, nlev, y, rec)
    % DFB output is a flat cell vector of length 2^nlev
    save_struct = struct('x', x, 'fname', fname, 'nlev', nlev, 'rec', rec);
    for k = 1:length(y)
        save_struct.(sprintf('y_%d', k)) = y{k};
    end
    fields = fieldnames(save_struct);
    for i = 1:length(fields)
        eval([fields{i} ' = save_struct.(''' fields{i} ''');']);
    end
    cmd = sprintf('save(''-v6'', ''%s''', filename);
    for i = 1:length(fields)
        cmd = [cmd ', ''' fields{i} ''''];
    end
    cmd = [cmd ');'];
    eval(cmd);
end


function save_pdfb(filename, x, pfilt, dfilt, nlevs, y, c, s, rec)
    % y is a nested cell: y{1} is lowpass (matrix), y{l} for l>=2 is a
    % cell of directional subbands.
    lowpass = y{1};
    save_struct = struct('x', x, 'pfilt', pfilt, 'dfilt', dfilt, ...
                         'nlevs', nlevs, 'c', c, 's', s, 'rec', rec, ...
                         'lowpass', lowpass);
    for L = 2:length(y)
        for k = 1:length(y{L})
            save_struct.(sprintf('layer_%d_dir_%d', L-1, k)) = y{L}{k};
        end
    end
    fields = fieldnames(save_struct);
    for i = 1:length(fields)
        eval([fields{i} ' = save_struct.(''' fields{i} ''');']);
    end
    cmd = sprintf('save(''-v6'', ''%s''', filename);
    for i = 1:length(fields)
        cmd = [cmd ', ''' fields{i} ''''];
    end
    cmd = [cmd ');'];
    eval(cmd);
end
