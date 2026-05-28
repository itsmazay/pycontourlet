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

    % Deterministic inputs across multiple shapes so parity tests catch
    % shape-dependent bugs. R<MN> is a fixed random matrix of size MxN.
    X16 = reshape(1:256, 16, 16) / 256;
    X32 = reshape(1:1024, 32, 32) / 1024;
    rand('state', 42);
    R32 = randn(32, 32);
    R16 = randn(16, 16);
    R64 = randn(64, 64);
    R16x24 = randn(16, 24);    % non-square, both dims even
    R8 = randn(8, 8);          % small input

    % shapes table for primitive functions: name -> matrix
    PRIM_SHAPES = struct( ...
        'sq32',   R32, ...
        'sq16',   R16, ...
        'sq64',   R64, ...
        'rect',   R16x24, ...
        'small8', R8);

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
    % resampc periodic mode (loops over multiple shapes for parity coverage)
    prim_shape_names = {'sq32', 'sq64', 'rect'};
    prim_shapes = {R32, R64, R16x24};
    for i = 1:length(prim_shapes)
        sn = prim_shape_names{i};
        XX = prim_shapes{i};
        for rt = [1, 2]
            for sh = [1, 2]
                x = XX; rtype = rt; shift = sh;
                y = resampc(XX, rt, sh, 'per');
                save('-v6', ...
                     fullfile(out_dir, sprintf('resampc_%s_t%d_s%d.mat', sn, rt, sh)), ...
                     'x', 'rtype', 'shift', 'y');
            end
        end
        for rt = 1:4
            x = XX; rtype = rt;
            y = resamp(XX, rt);
            save('-v6', fullfile(out_dir, sprintf('resamp_%s_t%d.mat', sn, rt)), ...
                 'x', 'rtype', 'y');
            y = resampz(XX, rt);
            save('-v6', fullfile(out_dir, sprintf('resampz_%s_t%d.mat', sn, rt)), ...
                 'x', 'rtype', 'y');
        end
    end

    % qupz: even rows or arbitrary shape OK (uses resampz)
    qupz_shape_names = {'sq16', 'sq32', 'rect'};
    qupz_shapes = {R16, R32, R16x24};
    for i = 1:length(qupz_shapes)
        sn = qupz_shape_names{i};
        XX = qupz_shapes{i};
        for tp = [1, 2]
            x = XX; qtype = tp;
            y = qupz(XX, tp);
            save('-v6', fullfile(out_dir, sprintf('qupz_%s_t%d.mat', sn, tp)), ...
                 'x', 'qtype', 'y');
        end
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
    % dup with rectangular input
    x = R16x24; step = [2, 2]; phase = [0, 0];
    y = dup(R16x24, [2, 2], [0, 0]);
    save('-v6', fullfile(out_dir, 'dup_rect_zero.mat'), 'x', 'step', 'phase', 'y');

    % qdown / qup with multiple shapes (need even rows + cols)
    qtypes = {'1r', '1c', '2r', '2c'};
    qd_shape_names = {'sq32', 'sq64', 'rect'};
    qd_shapes = {R32, R64, R16x24};
    for i = 1:length(qd_shapes)
        sn = qd_shape_names{i};
        XX = qd_shapes{i};
        for j = 1:length(qtypes)
            qt = qtypes{j};
            x = XX; qtype = qt;
            y = qdown(XX, qt);
            save('-v6', fullfile(out_dir, sprintf('qdown_%s_%s.mat', sn, qt)), ...
                 'x', 'qtype', 'y');
            rec = qup(y, qt);
            save('-v6', fullfile(out_dir, sprintf('qup_%s_%s.mat', sn, qt)), ...
                 'y', 'qtype', 'rec');
        end
    end

    % pdown / pup with multiple shapes
    for i = 1:length(qd_shapes)
        sn = qd_shape_names{i};
        XX = qd_shapes{i};
        for pt = 1:4
            x = XX; ptype = pt;
            y = pdown(XX, pt);
            save('-v6', fullfile(out_dir, sprintf('pdown_%s_t%d.mat', sn, pt)), ...
                 'x', 'ptype', 'y');
            rec = pup(y, pt);
            save('-v6', fullfile(out_dir, sprintf('pup_%s_t%d.mat', sn, pt)), ...
                 'y', 'ptype', 'rec');
        end
    end

    %% ---- Polyphase decomposition / reconstruction -----------------------
    for i = 1:length(qd_shapes)
        sn = qd_shape_names{i};
        XX = qd_shapes{i};
        for j = 1:length(qtypes)
            qt = qtypes{j};
            x = XX; qtype = qt;
            [p0, p1] = qpdec(XX, qt);
            save('-v6', fullfile(out_dir, sprintf('qpdec_%s_%s.mat', sn, qt)), ...
                 'x', 'qtype', 'p0', 'p1');
            x_rec = qprec(p0, p1, qt);
            save('-v6', fullfile(out_dir, sprintf('qprec_%s_%s.mat', sn, qt)), ...
                 'p0', 'p1', 'qtype', 'x_rec');
        end
        for pt = 1:4
            x = XX; ptype = pt;
            [p0, p1] = ppdec(XX, pt);
            save('-v6', fullfile(out_dir, sprintf('ppdec_%s_t%d.mat', sn, pt)), ...
                 'x', 'ptype', 'p0', 'p1');
            x_rec = pprec(p0, p1, pt);
            save('-v6', fullfile(out_dir, sprintf('pprec_%s_t%d.mat', sn, pt)), ...
                 'p0', 'p1', 'ptype', 'x_rec');
        end
    end

    %% ---- Extension / filtering primitives -------------------------------
    ext_shape_names = {'sq32', 'sq64', 'rect'};
    ext_shapes = {R32, R64, R16x24};
    for i = 1:length(ext_shapes)
        sn = ext_shape_names{i};
        XX = ext_shapes{i};
        x = XX; ru = 2; rd = 3; cl = 1; cr = 4; extmod = 'per';
        y = extend2(XX, 2, 3, 1, 4, 'per');
        save('-v6', fullfile(out_dir, sprintf('extend2_%s_per.mat', sn)), ...
             'x', 'ru', 'rd', 'cl', 'cr', 'extmod', 'y');

        x = XX; ru = 1; rd = 1; cl = 0; cr = 0; extmod = 'qper_row';
        y = extend2(XX, 1, 1, 0, 0, 'qper_row');
        save('-v6', fullfile(out_dir, sprintf('extend2_%s_qper_row.mat', sn)), ...
             'x', 'ru', 'rd', 'cl', 'cr', 'extmod', 'y');

        x = XX; ru = 1; rd = 1; cl = 0; cr = 0; extmod = 'qper_col';
        y = extend2(XX, 1, 1, 0, 0, 'qper_col');
        save('-v6', fullfile(out_dir, sprintf('extend2_%s_qper_col.mat', sn)), ...
             'x', 'ru', 'rd', 'cl', 'cr', 'extmod', 'y');
    end

    [h, g] = pfilters('9-7');
    for i = 1:length(ext_shapes)
        sn = ext_shape_names{i};
        XX = ext_shapes{i};
        x = XX; f1 = h; f2 = h; extmod = 'per';
        y = sefilter2(XX, h, h, 'per');
        save('-v6', fullfile(out_dir, sprintf('sefilter2_%s_per.mat', sn)), ...
             'x', 'f1', 'f2', 'extmod', 'y');

        f = h' * h;
        x = XX; extmod = 'per';
        y = efilter2(XX, h' * h, 'per');
        save('-v6', fullfile(out_dir, sprintf('efilter2_%s_per.mat', sn)), ...
             'x', 'f', 'extmod', 'y');
    end

    %% ---- Laplacian pyramid / wavelet ------------------------------------
    pf = {'9-7', '5-3', 'Burt'};
    lp_shape_names = {'sq32', 'sq64', 'rect'};
    lp_shapes = {R32, R64, R16x24};
    for i = 1:length(pf)
        n = pf{i};
        [h, g] = pfilters(n);
        for j = 1:length(lp_shapes)
            sn = lp_shape_names{j};
            XX = lp_shapes{j};
            [c, d] = lpdec(XX, h, g);
            rec = lprec(c, d, h, g);
            x = XX;
            save('-v6', fullfile(out_dir, sprintf('lpdec_%s_%s.mat', sn, slugify(n))), ...
                 'x', 'h', 'g', 'c', 'd');
            save('-v6', fullfile(out_dir, sprintf('lprec_%s_%s.mat', sn, slugify(n))), ...
                 'c', 'd', 'h', 'g', 'rec');
        end
    end

    [h, g] = pfilters('9-7');
    wfb_shape_names = {'sq32', 'sq64'};
    wfb_shapes = {R32, R64};
    for i = 1:length(wfb_shapes)
        sn = wfb_shape_names{i};
        XX = wfb_shapes{i};
        [LL, LH, HL, HH] = wfb2dec(XX, h, g);
        rec = wfb2rec(LL, LH, HL, HH, h, g);
        x = XX;
        save('-v6', fullfile(out_dir, sprintf('wfb2_%s_9_7.mat', sn)), ...
             'x', 'h', 'g', 'LL', 'LH', 'HL', 'HH', 'rec');
    end

    %% ---- DFB ladder (pkva) and general (cd) -----------------------------
    % DFB needs square input divisible by 2^nlev. Use sq32 and sq64.
    dfb_shape_names = {'sq32', 'sq64'};
    dfb_shapes = {R32, R64};
    for i = 1:length(dfb_shapes)
        sn = dfb_shape_names{i};
        XX = dfb_shapes{i};
        for nlev = 1:3
            x = XX; fname = 'pkva';
            y = dfbdec_l(XX, 'pkva', nlev);
            rec = dfbrec_l(y, 'pkva');
            save_dfb(fullfile(out_dir, sprintf('dfb_l_pkva_%s_n%d.mat', sn, nlev)), ...
                     x, fname, nlev, y, rec);
        end
        df = {'cd', '9-7'};
        for j = 1:length(df)
            nm = df{j};
            for nlev = 1:3
                x = XX; fname = nm;
                y = dfbdec(XX, nm, nlev);
                rec = dfbrec(y, nm);
                save_dfb(fullfile(out_dir, ...
                                  sprintf('dfb_%s_%s_n%d.mat', slugify(nm), sn, nlev)), ...
                         x, fname, nlev, y, rec);
            end
        end
    end

    %% ---- PDFB end-to-end ------------------------------------------------
    pdfb_shape_names = {'sq32', 'sq64'};
    pdfb_shapes = {R32, R64};
    for i = 1:length(pdfb_shapes)
        sn = pdfb_shape_names{i};
        XX = pdfb_shapes{i};
        nlevs = [2, 3];
        y = pdfbdec(XX, '9-7', 'pkva', nlevs);
        [c, s] = pdfb2vec(y);
        rec = pdfbrec(y, '9-7', 'pkva');
        save_pdfb(fullfile(out_dir, sprintf('pdfb_%s_9_7_pkva_2_3.mat', sn)), ...
                  XX, '9-7', 'pkva', nlevs, y, c, s, rec);
    end

    %% ---- snr -------------------------------------------------------------
    in = R32;
    est = R32 + 0.05 * randn(32, 32);
    r = SNR(R32, est);
    save('-v6', fullfile(out_dir, 'snr_demo.mat'), 'in', 'est', 'r');

    %% ---- showpdfb (display image rendered from PDFB output) -------------
    % Use a small input + simple decomposition so the rendered image is small.
    % The MATLAB script in showpdfb.m calls image() / axis at the end which
    % opens a figure; we want only the displayIm matrix.
    showpdfb_save_fixtures(out_dir, R32);

    fprintf('Done.\n');
end


function showpdfb_save_fixtures(out_dir, x)
    % Pre-compute showpdfb output for several configurations and save the
    % resulting displayIm matrices for parity testing.
    nlevs = [2, 3];
    y = pdfbdec(x, '9-7', 'pkva', nlevs);
    % MATLAB's showpdfb calls image() at the end; suppress display by
    % creating an invisible figure for the duration.
    set(0, 'DefaultFigureVisible', 'off');
    fig = figure('Visible', 'off');
    cleanup_obj = onCleanup(@() close(fig));

    displayIm = showpdfb(y, 'auto2', 'others', 2, 6, 'abs', 1);
    save('-v6', fullfile(out_dir, 'showpdfb_auto2.mat'), 'x', 'displayIm');

    displayIm = showpdfb(y, 'auto1', 'others', 2, 6, 'abs', 1);
    save('-v6', fullfile(out_dir, 'showpdfb_auto1.mat'), 'x', 'displayIm');

    % Threshold mode: keep the K most significant coefficients
    displayIm = showpdfb(y, 200, 'others', 2, 6, 'abs', 1);
    save('-v6', fullfile(out_dir, 'showpdfb_thresh200.mat'), 'x', 'displayIm');

    % auto3 with a wavelet layer
    nlevs2 = [0, 3];
    y2 = pdfbdec(x, '9-7', 'pkva', nlevs2);
    displayIm = showpdfb(y2, 'auto3', 'others', 2, 6, 'abs', 1);
    save('-v6', fullfile(out_dir, 'showpdfb_auto3_wavelet.mat'), 'x', 'displayIm');
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
