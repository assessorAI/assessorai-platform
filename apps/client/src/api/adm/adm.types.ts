export type AdmSummaryResponse = {
  users: {
    total: number;
    active: number;
    inactive: number;
  };
};

export type SendPasswordResetRequest = {
  user_ids?: number[];
  emails?: string[];
};
