close all

M = csvread('tamit.csv', 1, 0);
M = M(1:100, :);

% starts = csvread('tamitstart.csv', 1, 0);
% M(:, 2:10) = M(:, 2:10) - repmat(starts, 50000, 1);

s = size(M);
n = s(1);

tamit = M(:, 1);
indicators = M(:, 1:10);

% Shift the tamit indicator by 1.
indicators(1:end-1, 1) = indicators(2:end, 1);

% Make the indicators positive.
indicatorPos = indicators;
indicatorPos(:,3) = indicatorPos(:,3) + ones(n, 1);
indicatorPos(:,6) = indicatorPos(:,6) + ones(n, 1);
indicatorPos(:,8) = indicatorPos(:,8) + 10 * ones(n, 1);

% Get dx.
dx = diff(indicatorPos(:, 2:end));

% Get dx/x.
dxx = log(indicatorPos(2:end, 2:end)) - log(indicatorPos(1:end-1, 2:end));

X = [indicatorPos(2:end, :) dx dxx ones(n-1, 1)];
y = tamit(2:end, 1);

[b, bint, r] = regress(y, X);
figure();
plot(r);

coef = [bint(:,1) b bint(:,2)];

disp('Mean:')
mean(abs(r))

% Plot to see how well the model looks.
Y = X * b;
figure();
hold on;
plot([NaN; Y]);
plot(y);