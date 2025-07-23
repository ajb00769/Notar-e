import { ComponentFixture, TestBed } from '@angular/core/testing';

import { DashboardBlockchainStatus } from './dashboard-blockchain-status';

describe('DashboardBlockchainStatus', () => {
  let component: DashboardBlockchainStatus;
  let fixture: ComponentFixture<DashboardBlockchainStatus>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [DashboardBlockchainStatus]
    })
    .compileComponents();

    fixture = TestBed.createComponent(DashboardBlockchainStatus);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
