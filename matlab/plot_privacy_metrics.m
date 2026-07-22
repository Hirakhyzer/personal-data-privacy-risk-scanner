function plot_privacy_metrics(outputDir)
%PLOT_PRIVACY_METRICS Plot synthetic privacy-risk metrics exported by Python.
%   plot_privacy_metrics('outputs') reads CSV files from outputs/results and
%   writes MATLAB figures to outputs/figures_matlab.

if nargin < 1
    outputDir = 'outputs';
end
resultsDir = fullfile(outputDir, 'results');
figDir = fullfile(outputDir, 'figures_matlab');
if ~exist(figDir, 'dir')
    mkdir(figDir);
end

riskPath = fullfile(resultsDir, 'synthetic_document_risk.csv');
if exist(riskPath, 'file')
    risk = readtable(riskPath);
    figure('Visible','off');
    histogram(risk.privacy_risk_score);
    title('Document privacy-risk score distribution');
    xlabel('Privacy risk score');
    ylabel('Documents');
    saveas(gcf, fullfile(figDir, 'matlab_privacy_risk_distribution.png'));
    close(gcf);
end

entityPath = fullfile(resultsDir, 'synthetic_entity_type_summary.csv');
if exist(entityPath, 'file')
    entities = readtable(entityPath);
    figure('Visible','off');
    bar(categorical(entities.entity_type), entities.finding_count);
    title('Sensitive entity findings by type');
    ylabel('Findings');
    xtickangle(45);
    saveas(gcf, fullfile(figDir, 'matlab_entity_type_counts.png'));
    close(gcf);
end
end
